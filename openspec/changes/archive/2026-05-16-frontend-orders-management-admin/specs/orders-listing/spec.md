## MODIFIED Requirements

### Requirement: Orders listing includes user identifier and management actions
The admin orders listing table SHALL include a user identifier column and per-row management actions in addition to the existing read-only columns. The table SHALL retain all existing columns (ID, fecha, total, estado) and add: a checkbox column for bulk selection, a "Usuario" column showing `usuario_email` (or `#usuario_id` fallback), and a "Cambiar estado" action button alongside the existing "Ver detalle" button.

#### Scenario: User column shows email when available
- **WHEN** the API response includes `usuario_email` on order items
- **THEN** the "Usuario" column SHALL display the email string

#### Scenario: User column shows ID fallback when email absent
- **WHEN** the API response does not include `usuario_email` on order items
- **THEN** the "Usuario" column SHALL display `#<usuario_id>` as fallback text

#### Scenario: Row has both detail and state-change actions
- **WHEN** the orders management table renders for ADMIN or PEDIDOS role
- **THEN** each row SHALL have both a "Ver detalle" button (navigates to `/admin/pedidos/:id`) and a "Cambiar estado" button (opens StateTransitionModal)

#### Scenario: Existing filters continue to work
- **WHEN** admin selects a filter by estado or date range
- **THEN** the orders query SHALL update and the table SHALL display only matching orders (unchanged behavior)
