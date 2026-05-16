## ADDED Requirements

### Requirement: Admin can view orders with full management columns
The system SHALL render an `OrdersManagementTable` at `/admin/pedidos` that includes, for each order row: a checkbox for selection, order ID, user email (or `#usuario_id` if email not in API response), creation datetime, total in ARS, FSM status badge, and action buttons ("Ver detalle", "Cambiar estado").

#### Scenario: Table renders with full columns for ADMIN role
- **WHEN** an authenticated user with role ADMIN navigates to `/admin/pedidos`
- **THEN** the table SHALL display columns: checkbox, #Pedido, Usuario, Fecha, Total, Estado, Acciones

#### Scenario: Table is accessible as semantic grid
- **WHEN** the management table is rendered
- **THEN** the `<table>` element SHALL have `role="grid"`, `<th>` elements SHALL have `scope="col"`, and each data row SHALL have `role="row"`

---

### Requirement: Admin can change a single order's FSM state from the panel
The system SHALL provide a "Cambiar estado" button per order row that opens `StateTransitionModal`. The modal SHALL display only the valid next states permitted by the FSM for the order's current state. Submitting the modal SHALL call `PATCH /api/v1/pedidos/{id}/estado` with `{ nuevo_estado_id }` and invalidate the orders query.

#### Scenario: Valid transitions shown for CONFIRMADO order
- **WHEN** admin clicks "Cambiar estado" on a CONFIRMADO (estado_id=2) order
- **THEN** the modal SHALL show exactly two options: "EN PREPARACIÓN" and "CANCELADO"

#### Scenario: No transition options for terminal order
- **WHEN** admin clicks "Cambiar estado" on an ENTREGADO (estado_id=5) or CANCELADO (estado_id=6) order
- **THEN** the modal SHALL display a message "Este pedido está en estado terminal" and SHALL NOT show any radio options or a submit button

#### Scenario: Successful state transition
- **WHEN** admin selects a valid next state and clicks "Confirmar"
- **THEN** the system SHALL call `PATCH /api/v1/pedidos/{id}/estado`, close the modal on success, show a success toast, and refresh the orders list

#### Scenario: Failed state transition (API error)
- **WHEN** the PATCH call returns a 4xx or 5xx error
- **THEN** the modal SHALL remain open and show the error message from the API response

---

### Requirement: Admin can select multiple orders with checkboxes
The system SHALL render a checkbox in the first column of every data row and a "select all" checkbox in the header. The header checkbox SHALL display as indeterminate when some (but not all) rows on the current page are selected.

#### Scenario: Selecting individual row
- **WHEN** admin clicks a row's checkbox
- **THEN** that order's ID SHALL be added to `ordersManagementStore.selectedIds` and the checkbox SHALL appear checked

#### Scenario: Select all on current page
- **WHEN** admin clicks the header checkbox while no rows are selected
- **THEN** all order IDs on the current page SHALL be added to `selectedIds` and the header checkbox SHALL appear checked

#### Scenario: Deselect all
- **WHEN** admin clicks the header checkbox while all rows are selected
- **THEN** `selectedIds` SHALL be cleared and all row checkboxes SHALL appear unchecked

#### Scenario: Indeterminate header checkbox
- **WHEN** some but not all rows on the current page are selected
- **THEN** the header checkbox DOM property `indeterminate` SHALL be `true`

---

### Requirement: BulkActionsBar appears when selection is non-empty
The system SHALL render `BulkActionsBar` as a sticky bar at the top or bottom of the table when `selectedIds.size > 0`. The bar SHALL display the count of selected orders and offer "Cambiar estado masivo" and "Cancelar seleccionados" actions.

#### Scenario: Bar visible with selection
- **WHEN** one or more order rows are selected
- **THEN** `BulkActionsBar` SHALL be visible and SHALL display "X pedidos seleccionados"

#### Scenario: Bar hidden with no selection
- **WHEN** `selectedIds` is empty
- **THEN** `BulkActionsBar` SHALL NOT be rendered (not just hidden)

---

### Requirement: Admin can bulk-cancel selected orders
The system SHALL allow the admin to cancel all selected orders. Before executing, the system SHALL show a confirmation dialog listing the count of orders to cancel. On confirmation, the system SHALL issue `DELETE /api/v1/pedidos/{id}` for each selected order via `Promise.allSettled` and display a summary toast (e.g., "3 de 5 pedidos cancelados").

#### Scenario: Confirmation dialog before bulk cancel
- **WHEN** admin clicks "Cancelar seleccionados" in BulkActionsBar
- **THEN** a confirmation modal SHALL appear asking "¿Cancelar X pedidos seleccionados?"

#### Scenario: Successful bulk cancel
- **WHEN** admin confirms the bulk cancel dialog and all DELETE calls succeed
- **THEN** the system SHALL show a success toast "X pedidos cancelados", clear `selectedIds`, and refresh the orders list

#### Scenario: Partial bulk cancel failure
- **WHEN** admin confirms bulk cancel and some DELETE calls fail (e.g., orders already terminal)
- **THEN** the system SHALL show a warning toast indicating partial success (e.g., "3 de 5 pedidos cancelados. 2 no pudieron cancelarse.")

---

### Requirement: Admin can bulk-advance selected orders to a common next state
The system SHALL allow the admin to advance all selected orders to the same FSM state. The bulk state-change is only available when all selected orders share the same current estado_pedido_id. If selected orders have mixed states, the system SHALL show a warning and disable the "Cambiar estado masivo" button.

#### Scenario: Mixed-state selection disables bulk state change
- **WHEN** admin selects orders with different `estado_pedido_id` values
- **THEN** the "Cambiar estado masivo" button in BulkActionsBar SHALL be disabled with tooltip "Seleccioná pedidos del mismo estado para cambiar en bloque"

#### Scenario: Bulk state change modal for same-state selection
- **WHEN** all selected orders share the same `estado_pedido_id` and admin clicks "Cambiar estado masivo"
- **THEN** `StateTransitionModal` SHALL open in bulk mode showing valid transitions for that shared state

#### Scenario: Successful bulk state advancement
- **WHEN** admin confirms a bulk state change and all PATCH calls succeed
- **THEN** the system SHALL show a success toast, clear `selectedIds`, and refresh the orders list

---

### Requirement: Admin can filter orders by advanced criteria
The system SHALL provide `OrderFiltersPanel` with additional filter fields: user email (text, partial match), total mínimo (number), total máximo (number). These filters SHALL be stored in `ordersFilterStore` (extended) and passed as query parameters to `GET /api/v1/pedidos`. Filters reset on page reload (no persist middleware).

#### Scenario: Filter by user email
- **WHEN** admin types an email in the "Email usuario" filter field
- **THEN** the orders query SHALL include `q=<email>` and the table SHALL update to show matching orders

#### Scenario: Filter by total range
- **WHEN** admin sets total mínimo = 500 and total máximo = 2000
- **THEN** the query SHALL include `total_min=500&total_max=2000` (if backend supports it) or client-side filter if not

#### Scenario: Reset all filters
- **WHEN** admin clicks "Limpiar filtros"
- **THEN** all filter fields (including email and total range) SHALL reset to empty/null and the orders query SHALL reset to unfiltered

---

### Requirement: Responsive layout — table on desktop, cards on mobile
The management panel SHALL render the `OrdersManagementTable` on `md+` breakpoints and a card-based list (`OrderCard` per order) on `< md` breakpoints. `BulkActionsBar` and modals SHALL function on both layouts.

#### Scenario: Mobile layout shows cards
- **WHEN** viewport width is below `md` (768px)
- **THEN** the table SHALL be hidden (`hidden md:block`) and card list SHALL be visible

#### Scenario: Desktop layout shows table
- **WHEN** viewport width is `md` or above
- **THEN** `OrdersManagementTable` SHALL be visible and card list SHALL be hidden
