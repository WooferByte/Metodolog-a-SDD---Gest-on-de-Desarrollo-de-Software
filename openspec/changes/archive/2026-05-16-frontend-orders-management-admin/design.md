## Context

The admin orders panel at `/admin/pedidos` currently exposes `OrdersPanelPage`, which renders `OrdersFilters` + `OrdersTable`. The table is read-only: the only per-row action is "Ver detalle" (navigate to `/admin/pedidos/:id`). State transitions are only possible from the detail page (`OrderDetailPage`), which creates friction for ADMIN/PEDIDOS roles managing many orders sequentially.

The backend already exposes the full management API:
- `PATCH /api/v1/pedidos/{id}/estado` — FSM transition (already consumed by `useAdvanceOrderState`)
- `DELETE /api/v1/pedidos/{id}` — cancel (already consumed by `useCancelOrder`)

The FSM is deterministic:
```
1=PENDIENTE    → 6=CANCELADO
2=CONFIRMADO   → 3=EN_PREPARACIÓN | 6=CANCELADO
3=EN_PREPARACIÓN → 4=EN_CAMINO
4=EN_CAMINO    → 5=ENTREGADO
5=ENTREGADO    → (terminal)
6=CANCELADO    → (terminal)
```

Existing reusable pieces: `OrderStatusBadge`, `useOrders`, `useAdvanceOrderState`, `useCancelOrder`, `useOrdersFilterStore`, `OrdersSkeleton`.

## Goals / Non-Goals

**Goals:**
- Allow ADMIN/PEDIDOS roles to transition a single order's FSM state directly from the panel (without navigating to the detail page)
- Allow bulk cancel of multiple selected orders from the panel
- Allow bulk state advancement for orders that share the same current state
- Extend filters with user-email and total-range dimensions
- Keep existing read-only listing behavior intact and accessible (no regressions)
- Maintain WCAG AA accessibility: semantic table, ARIA roles, keyboard navigation, indeterminate checkbox state
- Responsive layout: table on `md+`, card list on mobile

**Non-Goals:**
- Inline editing of order fields (address, items, payment method)
- Real-time push updates (WebSocket/SSE) — polling via TanStack Query `refetchInterval` is acceptable
- New backend endpoints — all mutations use existing API
- Modifying the order detail page (`OrderDetailPage`)

## Decisions

### D1 — Extend `OrdersPanelPage` in-place rather than creating a parallel page

**Decision**: Rename/extend the existing `OrdersPanelPage.tsx` to `OrdersManagementPage.tsx` (or extend it in-place) and keep the route `/admin/pedidos` unchanged.

**Rationale**: A new page would require Router.tsx changes and risks leaving a dead route. Extending the existing page avoids duplication of the filter/pagination logic already present. The existing `OrdersTable` is replaced by the new `OrdersManagementTable`.

**Alternative considered**: Create a separate `/admin/pedidos/manage` route — rejected because it splits admin workflow across two URLs.

---

### D2 — New Zustand store `ordersManagementStore` for selection/bulk state

**Decision**: Add `ordersManagementStore` to `frontend/src/features/orders/store/` for: `selectedIds: Set<number>`, `isBulkPending: boolean`, and toggle/clearAll actions.

**Rationale**: Selection state is 100% client-side UI state — it does not belong in TanStack Query. Keeping it separate from `ordersFilterStore` maintains the single-responsibility principle and avoids `useShallow` sprawl.

**Alternative considered**: Co-locate selection state in component `useState` — rejected because `BulkActionsBar` and `OrdersManagementTable` are sibling components that both need access to selected IDs without prop-drilling.

---

### D3 — FSM transition map defined client-side as a constant

**Decision**: Define `FSM_TRANSITIONS: Record<number, number[]>` in `frontend/src/features/orders/constants/fsm.ts` as the authoritative client-side FSM map.

```ts
export const FSM_TRANSITIONS: Record<number, number[]> = {
  1: [6],           // PENDIENTE → CANCELADO
  2: [3, 6],        // CONFIRMADO → EN_PREPARACIÓN | CANCELADO
  3: [4],           // EN_PREPARACIÓN → EN_CAMINO
  4: [5],           // EN_CAMINO → ENTREGADO
  5: [],            // ENTREGADO (terminal)
  6: [],            // CANCELADO (terminal)
}
```

**Rationale**: The FSM is deterministic and defined in the spec. Hardcoding it client-side avoids an extra API round-trip to fetch valid transitions. If the backend rejects an invalid transition, the mutation's `onError` handler surfaces the toast error.

**Alternative considered**: Fetch valid transitions from a `/api/v1/pedidos/{id}/transitions` endpoint — rejected because no such endpoint exists; adding it is out of scope.

---

### D4 — `StateTransitionModal` validates FSM before enabling submit

**Decision**: `StateTransitionModal` receives `currentStatusId` and derives `validNextStates` from `FSM_TRANSITIONS`. Radio inputs render only valid next states. The "Confirmar" button is disabled if no state is selected or if the order is terminal.

**Rationale**: Prevents invalid PATCH calls and surfaces FSM constraints to the user clearly. The modal opens via a per-row "Cambiar estado" button in `OrdersManagementTable`.

---

### D5 — Bulk cancel uses `DELETE /api/v1/pedidos/{id}` sequentially via `Promise.allSettled`

**Decision**: Bulk cancel iterates `selectedIds`, issues one DELETE per order, collects results with `Promise.allSettled`, and reports partial failures in a summary toast.

**Rationale**: The backend has no batch-delete endpoint. `Promise.allSettled` avoids one failure blocking the rest. Partial failure is communicated (e.g., "3 de 5 pedidos cancelados").

**Alternative considered**: Sequential `await` per request — rejected because it's slower and a single failure would abort the rest.

---

### D6 — `OrderFiltersPanel` renders as a collapsible section below the search bar

**Decision**: The new filter panel is a collapsible `<details>`-based (or Zustand-toggled) section below `OrdersFilters`. It adds: `totalMin`, `totalMax` (number inputs), and `usuarioEmail` (text input). These 3 new fields are added to `ordersFilterStore`.

**Rationale**: Extending the existing `ordersFilterStore` avoids a second store for filters. The collapsible approach keeps the panel compact on load.

---

### D7 — `OrdersManagementTable` adds checkbox column + email column to existing table structure

**Decision**: `OrdersManagementTable` extends the current column set:
- Column 0 (new): checkbox — header has indeterminate "select all" logic
- Column 1: `# Pedido` (unchanged)
- Column 2 (new): Usuario Email (from `Order.usuario_email` — requires backend to include this field; if absent, show `usuario_id` as fallback)
- Column 3: Fecha
- Column 4: Total ARS
- Column 5: Estado (badge)
- Column 6: Acciones — "Ver detalle" + "Cambiar estado" buttons

**Rationale**: Additive approach reuses all existing rendering logic. The indeterminate checkbox uses `ref.indeterminate = true` (DOM property, not HTML attribute).

**Note on `usuario_email`**: The current `Order` type does not include `usuario_email`. The backend `GET /api/v1/pedidos` response may or may not include it. Task includes checking backend schema; if absent, show `#${usuario_id}` as fallback and log a TODO.

---

### D8 — Responsive: table on `md+`, `OrderCard` list on mobile

**Decision**: On `< md` breakpoints, hide the full table and render `OrderCard` components per order (already implemented). `BulkActionsBar` and `StateTransitionModal` work the same on both layouts.

**Rationale**: `OrderCard` is already in the codebase. Reusing it for mobile avoids duplicate card rendering logic.

---

### D9 — E2E tests mock backend with `page.route`

**Decision**: Playwright tests mock all API calls using `page.route('**/api/v1/pedidos**', ...)` following the `testing-e2e-playwright` skill patterns. Auth state is seeded via `loginAs(page, 'ADMIN')` helper.

**Rationale**: No live backend needed for CI. Mocks make tests deterministic and fast.

## Risks / Trade-offs

- **`usuario_email` field absent from `Order`** → The backend `GET /api/v1/pedidos` may not serialize `usuario_email`. The table degrades gracefully to `#usuario_id`. A follow-up change or the `orders-api-endpoints` change may need to add the field to the serializer. Low risk: the UI has a defined fallback.

- **Bulk `Promise.allSettled` under rate limiting** → The backend has rate limiting (`slowapi`, 10 pedidos/usuario/hora). Bulk cancel of many orders may hit the limit mid-batch. Mitigation: show partial-success toast; the user can retry remaining orders.

- **Indeterminate checkbox cross-browser** → `<input type="checkbox" ref={...}>` with `ref.current.indeterminate = true` is DOM-only and not serializable as an HTML attribute. Mitigation: handle via `useEffect` on selection change (standard pattern).

- **`StateTransitionModal` FSM map drift** → If the backend FSM changes, the client-side `FSM_TRANSITIONS` becomes stale. Mitigation: the backend will reject invalid transitions via 422; the `onError` toast surfaces this. The constant is co-located in `features/orders/constants/fsm.ts` for easy update.

## Migration Plan

1. Create new files without modifying existing ones first (additive approach)
2. Extend `ordersFilterStore` with 3 new fields (backward compatible — new fields, no removals)
3. Replace `OrdersTable` usage in `OrdersPanelPage` with `OrdersManagementTable` (wraps same props + additions)
4. Extend `OrdersPanelPage` with `BulkActionsBar` and `StateTransitionModal` render logic
5. Optionally rename page file to `OrdersManagementPage.tsx` and update lazy import in Router.tsx
6. Run vitest + Playwright E2E — no backend changes needed for unit tests

**Rollback**: Revert the `OrdersPanelPage` import from `OrdersManagementTable` back to `OrdersTable`. All new components are additive; reverting one import is sufficient.

## Open Questions

- Does `GET /api/v1/pedidos` currently serialize `usuario_email` in the response? (Check `backend/pedidos/schemas.py` at apply time — task 1.1 covers this.)
- Should the "Cambiar estado masivo" bulk action require all selected orders to share the same current state, or should it allow mixed states with per-order FSM validation? (Decision: require same current state for simplicity — the modal shows a warning if selected orders have mixed states.)
