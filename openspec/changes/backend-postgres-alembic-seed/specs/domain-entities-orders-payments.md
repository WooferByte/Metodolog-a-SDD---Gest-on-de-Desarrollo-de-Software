# Specification: Domain Entities – Orders & Payments

Order management and payment tracking entities: EstadoPedido, Pedido, DetallePedido, HistorialEstadoPedido, FormaPago, Pago.

## ADDED Requirements

### Requirement: EstadoPedido Entity – Immutable State Reference

The system SHALL define six immutable order states as reference data for FSM (Finite State Machine) transitions.

#### Scenario: Order states are fixed
- **WHEN** application starts
- **THEN** exactly 6 EstadoPedido records exist:
  - `PENDIENTE` (initial state, awaiting confirmation)
  - `CONFIRMADO` (customer confirmed; preparing to cook)
  - `PREPARANDO` (actively being prepared)
  - `LISTO` (ready for pickup/delivery)
  - `ENTREGADO` (delivered to customer)
  - `CANCELADO` (cancelled by customer or store)
- **AND** each state has `id`, `nombre` (unique), `descripcion`
- **AND** no UPDATE, DELETE allowed after initialization

#### Scenario: Query order states
- **WHEN** application fetches available state transitions
- **THEN** query: `SELECT * FROM estado_pedido`
- **AND** returns all 6 states; used to populate UI dropdowns and validate FSM transitions

### Requirement: Pedido Entity with FSM States and Snapshots

The system SHALL store order header with current state, total price, and reference to delivery address.

#### Scenario: Create pedido
- **WHEN** customer places order with items, Pedido record created with:
  - `usuario_id` (FK to customer)
  - `estado_pedido_id` (FK to EstadoPedido, initially PENDIENTE)
  - `direccion_entrega_id` (FK to DireccionEntrega; may be NULL for pickup)
  - `total` (calculated sum of line items)
  - `subtotal` (sum before taxes/fees)
  - `descuento` (applied coupon or manual discount, optional)
  - `impuestos` (tax amount)
  - `costo_entrega` (shipping cost if applicable)
  - `numero_pedido` (unique human-readable number, e.g., "PED-2026-001234")
  - `observaciones` (customer notes, optional)
  - `razon_cancelacion` (NULL initially; set if order cancelled)
- **THEN** all fields stored; `creado_en`, `actualizado_en` set to current UTC
- **AND** `eliminado_en` set to NULL

#### Scenario: FSM state transition
- **WHEN** order state changed (e.g., PENDIENTE → CONFIRMADO)
- **THEN** new `estado_pedido_id` assigned
- **AND** `actualizado_en` updated to current UTC
- **AND** validation ensures legal transition (PREPARANDO → PENDIENTE not allowed)
- **AND** HistorialEstadoPedido record created for audit trail

#### Scenario: Soft delete pedido
- **WHEN** `pedido.eliminado_en` set to current timestamp
- **THEN** order hidden from normal queries
- **AND** related records (DetallePedido, HistorialEstadoPedido) remain intact
- **AND** payment history preserved for compliance

#### Scenario: Query customer orders
- **WHEN** customer views order history
- **THEN** query: `SELECT * FROM pedido WHERE usuario_id = ? AND eliminado_en IS NULL ORDER BY creado_en DESC`
- **AND** orders listed with most recent first

### Requirement: DetallePedido – Price & Name Snapshots with Excluded Ingredients

The system SHALL store line items with immutable price/name snapshots to prevent retroactive changes; support ingredient exclusions.

#### Scenario: Create line item with snapshots
- **WHEN** DetallePedido record created for each item in order with:
  - `pedido_id` (FK)
  - `producto_id` (FK; for reference only)
  - `precio_snapshot` (product price at order time, frozen)
  - `nombre_snapshot` (product name at order time, frozen)
  - `cantidad` (quantity ordered)
  - `subtotal` (precio_snapshot * cantidad)
  - `excluded_ingredients` (JSON array of ingredient IDs to exclude, default "[]")
- **THEN** all snapshots captured at order creation time
- **AND** `creado_en` set to current UTC

#### Scenario: Price snapshot prevents price changes
- **WHEN** product price updated after order placed
- **THEN** `detalle_pedido.precio_snapshot` remains unchanged
- **AND** order total unaffected
- **AND** revenue calculation uses `SUM(precio_snapshot * cantidad)`, not live product price

#### Scenario: Exclude optional ingredients
- **WHEN** customer excludes ingredient (e.g., "no onions" on a pizza)
- **THEN** `excluded_ingredients` stored as JSON: `[1, 3, 5]` (ingredient IDs)
- **AND** validation: ingredient must be marked `es_removible = true` in ProductoIngrediente
- **AND** kitchen receives instruction: "no ingredient #1, #3, #5"

#### Scenario: Query order items
- **WHEN** application fetches order details
- **THEN** query: `SELECT * FROM detalle_pedido WHERE pedido_id = ?`
- **AND** response includes: cantidad, precio_snapshot, nombre_snapshot, excluded_ingredients list
- **AND** no joins to product table needed (data fully contained in snapshots)

### Requirement: HistorialEstadoPedido – Append-Only Audit Trail

The system SHALL maintain immutable audit log of all order state changes with immutable timestamps and user/system tracking.

#### Scenario: Create audit record on state change
- **WHEN** order state transitions (e.g., PENDIENTE → CONFIRMADO)
- **THEN** HistorialEstadoPedido record created with:
  - `pedido_id` (FK)
  - `estado_pedido_id` (FK to new state)
  - `cambio_por` (user email or "SISTEMA" for automated changes)
  - `razon` (human-readable reason, optional; e.g., "Admin confirmed after payment")
  - `creado_en` (change timestamp)
- **AND** record is INSERT-ONLY; no UPDATE or DELETE allowed

#### Scenario: Enforce append-only constraint
- **WHEN** application attempts to UPDATE or DELETE from historial_estado_pedido
- **THEN** operation rejected at application layer
- **AND** database trigger can enforce (future); for now, developer discipline

#### Scenario: Query order state history
- **WHEN** customer views order timeline
- **THEN** query: `SELECT h.*, e.nombre FROM historial_estado_pedido h JOIN estado_pedido e ON h.estado_pedido_id = e.id WHERE h.pedido_id = ? ORDER BY h.creado_en ASC`
- **AND** returns chronological list of all state changes with timestamps and reasons
- **AND** proves regulatory compliance: no tampering possible (append-only design)

#### Scenario: Detect tampering
- **WHEN** audit reviewer checks HistorialEstadoPedido
- **THEN** missing records (gaps in creado_en timestamps) indicate possible tampering
- **AND** immutable design ensures integrity checks work (can't delete, can't update)

### Requirement: FormaPago Entity – Immutable Payment Method Reference

The system SHALL define payment methods as immutable reference data for payment processing.

#### Scenario: Payment methods are fixed
- **WHEN** application starts
- **THEN** exactly 3 FormaPago records exist:
  - `EFECTIVO` (cash payment, in-store only)
  - `MERCADOPAGO` (online payment via MercadoPago gateway)
  - `TARJETA` (credit/debit card, processed via MercadoPago)
- **AND** each method has `id`, `nombre` (unique), `descripcion`

#### Scenario: Query payment methods
- **WHEN** customer views checkout page
- **THEN** query: `SELECT * FROM forma_pago`
- **AND** response filters based on order context (e.g., pickup orders show EFECTIVO only)

### Requirement: Pago Entity with MercadoPago Tracking and Idempotency

The system SHALL record all payment transactions with external gateway tracking and idempotency keys.

#### Scenario: Create payment record
- **WHEN** payment initiated for order with:
  - `pedido_id` (FK)
  - `forma_pago_id` (FK to FormaPago)
  - `monto` (payment amount in ARS)
  - `estado` (e.g., PENDIENTE, COMPLETADO, RECHAZADO, REEMBOLSADO)
  - `referencia_externa` (transaction ID from MercadoPago; unique across payments)
  - `idempotency_key` (UUID; prevents duplicate charges if request retried)
  - `respuesta_gateway` (JSON response from MercadoPago API; contains full transaction details)
  - `intentos` (attempt count; incremented on retry)
- **THEN** payment record stored
- **AND** `creado_en` set to current UTC

#### Scenario: Idempotent payment creation
- **WHEN** client sends payment request with same `idempotency_key` twice (network retry)
- **THEN** application queries: `SELECT * FROM pago WHERE idempotency_key = ?`
- **AND** if found, return existing payment result (no duplicate charge)
- **AND** if not found, create new payment record

#### Scenario: Track MercadoPago transaction
- **WHEN** MercadoPago payment successful
- **THEN** `referencia_externa` set to MercadoPago transaction ID
- **AND** `estado` set to COMPLETADO
- **AND** `respuesta_gateway` stores full API response JSON (e.g., authorization code, card last 4 digits)
- **AND** order state transitions to CONFIRMADO automatically

#### Scenario: Handle payment failure
- **WHEN** MercadoPago payment declined
- **THEN** `estado` set to RECHAZADO
- **AND** `respuesta_gateway` stores decline reason (insufficient funds, card expired, etc.)
- **AND** order state remains PENDIENTE; customer can retry

#### Scenario: Payment refund
- **WHEN** order cancelled or customer requests refund
- **THEN** new Pago record created with:
  - `monto` = negative amount (refund value)
  - `estado` = REEMBOLSADO
  - `referencia_externa` = original transaction ID (linked for audit)
- **AND** MercadoPago API called to reverse charge
- **AND** payment audit trail shows original + refund

#### Scenario: Query payment history
- **WHEN** admin views payment records
- **THEN** query: `SELECT * FROM pago WHERE pedido_id = ? ORDER BY creado_en DESC`
- **AND** returns all attempts, successes, and refunds chronologically
- **AND** `respuesta_gateway` JSON available for investigation if dispute occurs
