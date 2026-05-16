## Why

El change `orders-fsm-backend` implementó toda la lógica de negocio de pedidos (service, repository, FSM, audit trail) pero sin exponerla vía HTTP. Este change agrega el router que conecta los 5 endpoints REST con el service existente, completando la capa de presentación del módulo de pedidos.

## What Changes

- Agregar 5 endpoints REST en `backend/pedidos/router.py`:
  - `POST /api/v1/pedidos` — crear pedido desde carrito validado (CLIENT, rate-limited 10/hora)
  - `GET /api/v1/pedidos` — listar pedidos del usuario autenticado (CLIENT, paginado)
  - `GET /api/v1/pedidos/{id}` — detalle de un pedido con líneas (CLIENT dueño o ADMIN)
  - `PATCH /api/v1/pedidos/{id}/estado` — avanzar estado FSM (ADMIN)
  - `DELETE /api/v1/pedidos/{id}` — cancelar pedido / soft delete (CLIENT solo PENDIENTE o ADMIN)
- Agregar método `count_by_usuario()` en `PedidoRepository` para paginación con total
- Agregar schema `PaginatedPedidosResponse` en `pedidos/schemas.py`
- Agregar tests de integración en `backend/tests/test_orders_api.py`:
  - 401/403 en todos los endpoints protegidos
  - Validaciones de ownership (403 si otro usuario accede al pedido)
  - Transiciones FSM inválidas (409)
  - Rate limiting en POST /pedidos
  - Soft delete: pedido con `eliminado_en` no aparece en listado ni detalle
- Todos los errores usan RFC 7807 (`type`, `title`, `status`, `detail`, `instance`)
- `response_model` explícito en todos los endpoints

## Capabilities

### New Capabilities

- `orders-api`: Exposición HTTP de la lógica de pedidos — CRUD con FSM, paginación, ownership checks, rate limiting y soft delete.

### Modified Capabilities

- `orders-fsm`: El router extiende el módulo de pedidos FSM ya implementado. Los requisitos de negocio no cambian — solo se agrega la capa de presentación HTTP sobre la lógica existente.

## Impact

- **Archivos modificados**: `backend/pedidos/router.py`, `backend/pedidos/repository.py`, `backend/pedidos/schemas.py`
- **Archivos nuevos**: `backend/tests/test_orders_api.py`
- **Sin cambios de modelo ni migración Alembic** — el schema de BD ya existe del change anterior
- **Sin cambios de frontend** — este change es backend puro
- **Dependencias**: slowapi (ya instalado), pytest-asyncio (ya instalado)
- **Impacto en otros módulos**: ninguno — el service existente no se modifica
