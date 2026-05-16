## Context

The `pedidos/` module was partially implemented during `checkout-pre-validation`. It has
`service.py` (validar_carrito only), `schemas.py` (validation + skeleton create schemas), and
`router.py` (POST /validar). The DB tables `pedidos`, `detalle_pedido`,
`historial_estado_pedido`, `estados_pedido` already exist and are seeded.

The UoW (`infrastructure/uow.py`) already exposes `uow.pedidos`, `uow.detalles_pedido`,
`uow.historial_estado_pedido`, and `uow.estados_pedido` as `BaseRepository[T]` instances.
Models `Pedido`, `DetallePedido`, `HistorialEstadoPedido` are already declared in
`core/models.py`. No schema changes required.

Constraint: this change is purely service/repository layer — no HTTP router additions. Those
come in `orders-api-endpoints`.

## Goals / Non-Goals

**Goals:**

- Implement `PedidoRepository` with FSM-aware operations: `create_with_details()`,
  `get_by_id_with_details()`, `list_by_usuario()`, `avanzar_estado()`.
- Implement `HistorialEstadoPedidoRepository` (append-only — only `append()` exposed).
- Implement service functions: `create_pedido()`, `avanzar_estado()`, `cancelar()`.
- Enforce FSM transition matrix at service layer (raise HTTP 409 for invalid transitions).
- Enforce that PENDIENTE → CONFIRMADO is SYSTEM/ADMIN only (RN-FS02).
- Decrement `Producto.stock_cantidad` atomically using `SELECT FOR UPDATE` (RN-PE04).
- Write price snapshot (`precio_snapshot`) and address snapshot (`direccion_snapshot`) at
  creation time — immutable after that.
- Rate-limit order creation to 10/usuario/hora (US-073) via slowapi.
- Write `HistorialEstadoPedido` rows for every transition (audit trail, append-only).
- Update UoW to expose typed `PedidoRepository` and `HistorialEstadoPedidoRepository`.
- Provide pytest tests in `backend/tests/test_orders_fsm.py` (≥ 60 % coverage for new code).

**Non-Goals:**

- No HTTP router endpoints in this change.
- No MercadoPago webhook integration (belongs to `pagos-mercadopago`).
- No push notifications or async background tasks.
- No admin override bypass logic for stock checks.
- No Alembic migration (tables already exist).

## Decisions

### D-01: Repository split — PedidoRepository vs. BaseRepository[Pedido]

**Decision**: Create a dedicated `pedidos/repository.py` with `PedidoRepository(BaseRepository[Pedido])`.

**Rationale**: `create_with_details()` needs a multi-step write (INSERT pedido → flush to get
ID → INSERT detalles → decrement stock with FOR UPDATE → INSERT historial). This logic is
too specific for the generic `BaseRepository`. Keeping it in a typed subclass respects the
architecture layer rule (Repository handles DB, not Service).

**Alternative considered**: Do all of this in the service. Rejected — service would directly
manipulate session, violating the "repository owns DB access" principle from `python-fastapi-ddd-skill`.

### D-02: HistorialEstadoPedido — separate file vs. part of pedidos/repository.py

**Decision**: Keep `HistorialEstadoPedidoRepository` in `pedidos/repository.py` (as a second
class in the same file, not a separate file).

**Rationale**: It is tightly coupled to order operations and small enough (1 method). Separate
file (`historial_repository.py`) adds unnecessary indirection for this scope.

### D-03: FSM transition table — where to declare

**Decision**: Declare the valid transition dict as a module-level constant in `pedidos/service.py`.

```python
VALID_TRANSITIONS: dict[int, list[int]] = {
    1: [2, 6],   # PENDIENTE → CONFIRMADO | CANCELADO
    2: [3, 6],   # CONFIRMADO → EN_PREPARACIÓN | CANCELADO
    3: [4],      # EN_PREPARACIÓN → EN_CAMINO
    4: [5],      # EN_CAMINO → ENTREGADO
    5: [],       # ENTREGADO — terminal
    6: [],       # CANCELADO — terminal
}
# States only System/webhook can set:
SYSTEM_ONLY_TARGETS: set[int] = {2}  # CONFIRMADO (RN-FS02)
```

**Rationale**: Single source of truth for the FSM, easy to test without DB. No enum class
needed — IDs are stable seeds (1-6), documented in AGENTS.md decisions.

**Alternative considered**: Store valid transitions in DB. Rejected — adds complexity and the
states are static by domain definition.

### D-04: SELECT FOR UPDATE — scope

**Decision**: Apply `with_for_update()` per-product inside `create_with_details()` when
fetching products to decrement stock. Lock only the product rows involved in the order.

**Rationale**: Narrow locking minimises contention. We don't need to lock the whole `pedidos`
table, only the `productos` rows being mutated. Consistent with RN-PE04 from the spec.

### D-05: Address snapshot format

**Decision**: Serialize `DireccionEntrega` fields to a compact JSON string and store in
`Pedido.direccion_snapshot` (VARCHAR). The field already exists in the schema as `Optional[str]`.

**Format**:
```json
{"alias":"Casa","linea1":"Av. Corrientes 1234","ciudad":"Buenos Aires","codigo_postal":"C1043"}
```

**Rationale**: Snapshot immutability is the goal, not queryability. A JSON string in a VARCHAR
column achieves this without a separate snapshot table or JSON column type.

### D-06: Rate limiting — where to apply

**Decision**: Apply `@limiter.limit("10/hour")` decorator at the **router** layer (when
`orders-api-endpoints` adds the POST /pedidos endpoint). The service itself doesn't enforce
rate limiting — that's a presentation-layer concern (slowapi pattern already used for login).

**Implication for this change**: `service.create_pedido()` does NOT include rate limit logic.
The spec documents the limit; enforcement is in the next change's router.

### D-07: UoW update strategy

**Decision**: Update `uow.pedidos` and `uow.historial_estado_pedido` properties to return
typed `PedidoRepository` / `HistorialEstadoPedidoRepository` instances respectively. Keep
`uow.detalles_pedido` as `BaseRepository[DetallePedido]` (used by repository layer directly
via session, not by UoW consumers).

**Rationale**: Typed repos surface domain methods to service layer. The service calls
`uow.pedidos.create_with_details(...)` not raw session operations.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| SELECT FOR UPDATE deadlock with concurrent orders for same product | Row-level locks in PostgreSQL are efficient; transactions are short-lived. If deadlock: asyncpg surfaces `DeadlockDetectedError` → UoW rollback → 503 response. |
| `ingredientes_excluidos` ARRAY(Integer) NULL handling | Pydantic schema defaults to `None`; SQLModel maps to `nullable=True`. Ensure `[]` (empty list) is coerced to `None` or `[]` consistently. Test both. |
| `HistorialEstadoPedido` rows piling up | Append-only is by design (audit). No cleanup needed. Indexed by `pedido_id`. |
| service.py growing large with 3+ functions | Acceptable for this scope. Split into `service_fsm.py` only if file exceeds 300 LOC. |
| `precio_snapshot` vs Decimal precision | Use Python `Decimal` throughout; PostgreSQL `NUMERIC(10,2)` handles this. Never use float. |

## Migration Plan

1. Apply this change (service/repo/schema layer only).
2. Run `pytest backend/tests/test_orders_fsm.py` to verify.
3. Next change (`orders-api-endpoints`) adds HTTP router and integrates with this service.
4. No Alembic migration required — tables exist.
5. Rollback: revert `pedidos/` and UoW changes. DB is unaffected.

## Open Questions

- **Q1**: Should `create_pedido()` also validate stock (re-check after `validar_carrito`)?
  **Tentative**: Yes — race condition between validate and create. The SELECT FOR UPDATE in
  `create_with_details()` is the authoritative stock check; raise HTTP 409 if stock insufficient
  at creation time.
- **Q2**: Should `avanzar_estado()` be restricted to PEDIDOS/ADMIN roles only?
  **Tentative**: Yes, enforced at router level in the next change (this service accepts
  `usuario_responsable_id` and records it in historial without role-checking).
