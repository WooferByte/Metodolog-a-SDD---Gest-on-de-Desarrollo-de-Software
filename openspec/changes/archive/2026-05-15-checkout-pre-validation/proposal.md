## Why

Before a user submits an order, critical conditions must be verified server-side to prevent invalid order creation: items with insufficient stock, stale prices in the cart, a missing delivery address, or an empty cart. Without this pre-flight check, the order creation endpoint would fail mid-transaction or silently create bad data, degrading user experience and corrupting inventory.

## What Changes

- **New backend endpoint** `POST /api/v1/pedidos/validar` (requires CLIENT auth) that accepts the cart contents + a selected address ID and returns a structured validation report.
- **New Pydantic v2 schemas**: `ValidarCarritoRequest` (list of items with `producto_id`, `cantidad`, `precio_carrito`) and `ValidarCarritoResponse` (structured report with stock issues, price changes, and flags).
- **New backend service logic** in `pedidos/service.py` (or a dedicated `pedidos/validation_service.py`) that performs all four checks atomically via UoW.
- **New repository methods** on `ProductoRepository` for batch stock/price lookup.
- **New frontend feature** `features/checkout/` with a `useCheckoutValidation` hook (TanStack Query) that fires the validation endpoint when the user navigates to the checkout page.
- **New frontend UI**: a `CheckoutValidationModal` or inline alert block that surfaces stock issues and price changes, requiring user confirmation before proceeding.
- No database schema changes — reads only against `productos` and `direcciones_entrega` tables.
- No Alembic migration required.

## Capabilities

### New Capabilities

- `checkout-pre-validation`: Backend validation endpoint that checks stock, current prices, address existence, and cart emptiness before order creation. Returns a structured report; does not mutate any state.
- `checkout-validation-ui`: Frontend hook + modal/alert UI that fires the validation on checkout entry and blocks proceeding if critical issues (empty cart, no address) are present; shows confirmable warnings for stock shortfalls and price changes.

### Modified Capabilities

- `zustand-cart-store`: The cart item shape must include `precio_carrito` (the price at the time of adding to cart) to support price-drift detection in the validation payload. This is an additive change to the existing `CartItem` type.

## Impact

- **Backend files**: `backend/pedidos/schemas.py` (new request/response schemas), `backend/pedidos/service.py` (new validation method), `backend/pedidos/router.py` (new endpoint), `backend/productos/repository.py` (new batch query methods).
- **Frontend files**: `frontend/src/features/checkout/` (new feature directory), `frontend/src/features/checkout/hooks/useCheckoutValidation.ts`, `frontend/src/features/checkout/components/CheckoutValidationModal.tsx`, `frontend/src/features/checkout/types/index.ts`, `frontend/src/store/cartStore.ts` (add `precio_carrito` field to `CartItem`).
- **Tests**: `backend/tests/test_checkout_validation.py` (pytest), `frontend/src/features/checkout/__tests__/useCheckoutValidation.test.ts` (vitest).
- **No external dependencies** added. No MercadoPago SDK needed yet (that is the `frontend-checkout` change).
- RFC 7807 error format for 422 responses (empty cart, no address). 200 with payload for soft warnings (stock/price).
