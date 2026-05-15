## Context

The food store currently allows users to add products to a client-side cart (Zustand + localStorage) and navigate to a checkout flow. However, there is no server-side pre-flight check before order creation. This means:

- A user could attempt to order 5 units of a product that only has 2 in stock.
- A product's price may have changed since it was added to the cart.
- A user may not have a delivery address configured.
- An empty cart could be submitted.

The `POST /api/v1/pedidos` endpoint (not yet implemented) would need to handle these failures transactionally, but doing so silently degrades the user experience. A dedicated validation endpoint allows the frontend to surface actionable feedback before commitment.

**Current state:**
- `backend/pedidos/schemas.py` — has `PedidoCreate` and `DetallePedidoCreate` schemas.
- `backend/productos/repository.py` — `ProductoRepository` has `list_active` and `count_active` but no batch-by-ID lookup.
- `backend/direcciones/` — module exists with its own repository.
- Frontend `cartStore` (Zustand v5) — stores `{ productoId, nombre, precio, cantidad, imagen_url }` per item.

**Constraints:**
- Carrito is 100% client-side. The backend does NOT have a cart table.
- Validation endpoint must be read-only (no mutations, no commit).
- Response for soft warnings uses HTTP 200; hard failures (empty cart, no address) use HTTP 422 with RFC 7807.

## Goals / Non-Goals

**Goals:**
- Implement `POST /api/v1/pedidos/validar` following the Router → Service → UoW → Repository layering.
- Detect four conditions: empty cart, missing address, insufficient stock, price drift.
- Return a structured `ValidarCarritoResponse` that the frontend can render without further API calls.
- Add `precio_carrito` field to the Zustand `CartItem` type so the frontend can send current cart prices for comparison.
- Implement `useCheckoutValidation` TanStack Query mutation that fires on checkout page entry.
- Implement `CheckoutValidationModal` that surfaces issues and blocks or warns appropriately.

**Non-Goals:**
- Creating the actual order (`POST /api/v1/pedidos`) — that is the `orders-fsm-backend` change.
- MercadoPago integration — that is `frontend-checkout`.
- Reserving stock or locking inventory — validation is advisory only.
- Implementing the address selection UI — addresses are read from the existing `GET /api/v1/direcciones`.

## Decisions

### D-01: Endpoint returns 200 for stock/price issues, 422 for structural failures

**Decision:** `carritoVacio=true` and `sinDireccion=true` return HTTP 422 (RFC 7807). All other combinations (stock shortfalls, price changes, or clean validation) return HTTP 200 with the `ValidarCarritoResponse` body.

**Rationale:** Stock and price issues are informational — the user should be allowed to acknowledge and proceed. Empty cart and no address are structural pre-conditions for any order and cannot be overridden by the user at this point without leaving the page.

**Alternative considered:** Return 422 for all failure modes. Rejected because it forces the frontend to parse error bodies differently depending on severity, complicating the UX.

### D-02: Batch stock/price lookup via single IN query (not N individual GETs)

**Decision:** Add `get_by_ids(product_ids)` to `ProductoRepository` that fetches all needed products in a single `SELECT ... WHERE id IN (...)` query.

**Rationale:** The cart can have N items. N round-trips to the DB inside a single request are unacceptable. A single batched query is O(1) DB round-trips.

**Alternative considered:** Reuse existing `list_active` with `q=None` and filter in Python. Rejected because `list_active` applies `disponible=True` and `eliminado_en IS NULL` filters — a product that has been soft-deleted or made unavailable should still surface as a validation error (not silently disappear from results).

### D-03: Validation service is a pure read — no UoW commit

**Decision:** The validation method in `pedidos/service.py` uses `async with uow:` for session management but never triggers a commit. UoW commit is automatic on context-manager exit only when `uow.commit()` is explicitly called — since we never call it, the UoW exits with a rollback/close only.

**Rationale:** This endpoint is advisory. No state changes. Keeping it inside UoW ensures consistent session lifecycle and allows accessing multiple repositories without opening multiple sessions.

**Alternative considered:** Dependency-inject the session directly into the service function. Rejected to maintain architectural consistency — all services use UoW.

### D-04: Price comparison uses tolerance threshold

**Decision:** A price is considered "changed" if `abs(precio_actual - precio_carrito) > 0.01` (1 centavo tolerance).

**Rationale:** Floating-point and NUMERIC(10,2) comparisons can produce trivial differences. A 1-cent threshold is imperceptible to users and avoids spurious warnings.

### D-05: Frontend fires validation as TanStack Query mutation, not a query

**Decision:** `useCheckoutValidation` is a `useMutation` hook, not a `useQuery`. It is called imperatively when the user navigates to checkout (via `useEffect` on mount or a "Proceed to Checkout" button click).

**Rationale:** The validation call is side-effect-adjacent (it reads the cart state at the moment of navigation). `useQuery` would refetch on window focus, causing unexpected modal appearances. `useMutation` gives the caller full control.

**Alternative considered:** `useQuery` with `enabled: false` and manual `refetch()`. Rejected as semantically misleading — validation is not a cacheable resource.

### D-06: CartItem gains precio_carrito field (additive change)

**Decision:** Add `precio_carrito: number` to the Zustand `CartItem` interface. This is set at the time of `addItem()` from the product's current `precio` field.

**Rationale:** The backend needs to know what price the user saw when adding the product. Without this, price-drift detection requires the frontend to store prices elsewhere or the backend to make assumptions.

**Impact:** Existing cart items in localStorage will not have `precio_carrito`. The migration strategy is: read `item.precio_carrito ?? item.precio` in the checkout hook — if undefined, use the cart-stored `precio` field as a fallback (this means no price-drift detection for items already in cart at deploy time, which is acceptable).

## Risks / Trade-offs

- **Race condition**: Between validation and actual order submission, stock could change again. Mitigation → the order creation endpoint (`orders-fsm-backend`) must re-validate stock atomically at write time. This endpoint is advisory, not authoritative.
- **Price tolerance edge case**: The 0.01 threshold may miss intentional 1-cent price adjustments. Mitigation → acceptable for a university project; can be made configurable via the `feature-flags` spec if needed.
- **localStorage backward compatibility**: Existing carts lack `precio_carrito`. Mitigation → fallback to `precio` field (D-06). No user-visible breakage.
- **CartItem shape divergence**: Zustand `CartItem` and the backend request schema must stay in sync. If one is updated without the other, silent type mismatches can occur. Mitigation → TypeScript strict mode catches frontend-side drift; the backend schema validates with Pydantic v2.

## Migration Plan

1. No Alembic migration required — endpoint is read-only against existing tables.
2. Deploy backend endpoint first; frontend feature is behind the new `/checkout` route which is not linked from navigation yet, so no rollout risk.
3. Rollback: remove the new endpoint registration from `pedidos/router.py` and delete the new frontend feature directory. No DB state to revert.

## Open Questions

- Should `sinDireccion` check for at least one active address for the user, or specifically a selected/default address? **Decision: check `es_predeterminada=True` first; if none exists, check `COUNT > 0` — if the user has addresses but none is default, return the first address ID and let the frontend pre-select it.** For the validation flag, `sinDireccion=True` only when the user has zero non-soft-deleted addresses.
- Should `productosInvalidos` include products that are `disponible=False` or `eliminado_en IS NOT NULL`? **Decision: yes — if a product in the cart is no longer available or has been deleted, it should appear in `productosInvalidos` so the frontend can prompt removal.**
