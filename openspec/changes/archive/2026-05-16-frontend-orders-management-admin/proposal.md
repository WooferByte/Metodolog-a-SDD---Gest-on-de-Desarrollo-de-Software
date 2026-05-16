## Why

The current `OrdersPanelPage` at `/admin/pedidos` provides basic order listing with read-only table and simple filters, but lacks the active management capabilities that ADMIN and PEDIDOS roles need: changing order states through the FSM, performing bulk operations on multiple orders simultaneously, and applying advanced multi-dimensional filters. These capabilities are required to efficiently manage order workflows without relying on backend-only tooling.

## What Changes

- **New component `OrdersManagementTable`**: Extends `OrdersTable` with checkbox selection column, full user-email column, and per-row FSM state-change action; replaces the existing `OrdersTable` usage on the admin panel
- **New component `StateTransitionModal`**: Modal that presents only the valid next states for a given order's current FSM position, calls `PATCH /api/v1/pedidos/{id}/estado`, and shows confirmatory feedback
- **New component `BulkActionsBar`**: Contextual bar that appears when ≥1 row is selected; shows selected count, "Cambiar estado masivo" and "Cancelar seleccionados" actions; requires a second confirmation modal before executing
- **New component `OrderFiltersPanel`**: Expanded filter UI (lateral panel or collapsible dropdown) adding total-range and user-email filters on top of the existing estado/fechas filters
- **New Zustand slice `ordersManagementStore`**: Tracks selected row IDs and bulk-action in-progress state (client-only — never server data)
- **Updated `OrdersPanelPage`**: Integrates all new components; replaced by a richer `OrdersManagementPage` (or the existing page is extended in-place under the same route)
- **New E2E tests** (`frontend/e2e/admin/orders-management.spec.ts`): Playwright coverage for filter-by-estado, row selection, FSM transition, and bulk cancel confirmation flow

## Capabilities

### New Capabilities

- `admin-orders-management`: Admin panel for active order management — FSM state transitions per order, bulk state-change and cancel, advanced multi-field filtering; accessible table with checkbox selection

### Modified Capabilities

- `orders-listing`: The existing listing capability is extended — user-email column added, checkbox column added, row-level state-change action added; query parameters unchanged (same API endpoints)

## Impact

- **Files modified**: `frontend/src/pages/OrdersPanelPage.tsx` (extended or replaced with `OrdersManagementPage.tsx`)
- **Files created**:
  - `frontend/src/features/orders/components/OrdersManagementTable.tsx`
  - `frontend/src/features/orders/components/StateTransitionModal.tsx`
  - `frontend/src/features/orders/components/BulkActionsBar.tsx`
  - `frontend/src/features/orders/components/OrderFiltersPanel.tsx`
  - `frontend/src/features/orders/store/ordersManagementStore.ts`
  - `frontend/e2e/admin/orders-management.spec.ts`
- **APIs consumed** (already implemented in backend):
  - `GET /api/v1/pedidos` — listing with filters (unchanged)
  - `PATCH /api/v1/pedidos/{id}/estado` — FSM transition (already used by `useAdvanceOrderState`)
  - `DELETE /api/v1/pedidos/{id}` — cancel (already used by `useCancelOrder`)
- **Dependencies**: No new npm packages needed; reuses `lucide-react`, Tailwind v4 tokens, Zustand v5, TanStack Query v5
- **Route**: `/admin/pedidos` — same route, same `ProtectedRoute` guard (roles: ADMIN, PEDIDOS)
