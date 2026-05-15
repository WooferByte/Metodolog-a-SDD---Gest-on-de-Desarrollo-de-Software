## ADDED Requirements

### Requirement: Order creation with snapshot and stock decrement
The system SHALL create a new order by: (1) validating all products are available and have
sufficient stock using SELECT FOR UPDATE, (2) recording price_snapshot and nombre_snapshot
per line item from current DB values, (3) serializing the delivery address to
direccion_snapshot JSON string, (4) decrementing Producto.stock_cantidad atomically for
each line item, (5) inserting an initial HistorialEstadoPedido row with
estado_anterior_id=NULL and estado_nuevo_id=1 (PENDIENTE). All steps MUST occur in a single
database transaction managed by the UoW context manager.

#### Scenario: Successful order creation
- **WHEN** a CLIENT submits a valid PedidoCreate request with in-stock products and a valid address
- **THEN** the system creates Pedido with estado_pedido_id=1 (PENDIENTE), calculates total as
  sum of (precio_snapshot * cantidad) for all detalles, decrements stock for each product,
  writes one HistorialEstadoPedido row with estado_anterior_id=NULL, and returns the created Pedido

#### Scenario: Insufficient stock at creation time
- **WHEN** a CLIENT submits a PedidoCreate where at least one product has stock_cantidad < requested cantidad
- **THEN** the system raises HTTP 409 with RFC 7807 body indicating which product is out of stock
  and rolls back all changes

#### Scenario: Product not available or soft-deleted
- **WHEN** a CLIENT submits a PedidoCreate referencing a product with disponible=False or eliminado_en IS NOT NULL
- **THEN** the system raises HTTP 422 and rolls back all changes

#### Scenario: Invalid delivery address
- **WHEN** a CLIENT submits a PedidoCreate with a direccion_entrega_id that does not belong to the user
- **THEN** the system raises HTTP 403 and does not create the order

### Requirement: FSM state transition enforcement
The system SHALL enforce the following valid transitions only:

| From | To | Actor |
|------|-----|-------|
| PENDIENTE(1) | CONFIRMADO(2) | SYSTEM/webhook only |
| PENDIENTE(1) | CANCELADO(6) | CLIENT or ADMIN |
| CONFIRMADO(2) | EN_PREPARACIÓN(3) | PEDIDOS or ADMIN |
| CONFIRMADO(2) | CANCELADO(6) | ADMIN only |
| EN_PREPARACIÓN(3) | EN_CAMINO(4) | PEDIDOS or ADMIN |
| EN_CAMINO(4) | ENTREGADO(5) | PEDIDOS or ADMIN |

CANCELADO(6) and ENTREGADO(5) SHALL be terminal states — no transitions allowed FROM them.
Every transition MUST write one HistorialEstadoPedido row (append-only).

#### Scenario: Valid FSM transition
- **WHEN** avanzar_estado() is called with a valid (current_state → new_state) pair
- **THEN** the system updates Pedido.estado_pedido_id to the new state, writes a HistorialEstadoPedido
  row with estado_anterior_id=current_state and estado_nuevo_id=new_state, and returns the updated Pedido

#### Scenario: Invalid FSM transition
- **WHEN** avanzar_estado() is called with an invalid (current_state → new_state) pair
  (e.g., PENDIENTE → EN_CAMINO or ENTREGADO → PENDIENTE)
- **THEN** the system raises HTTP 409 with RFC 7807 body "Transición de estado inválida" and
  does NOT write any HistorialEstadoPedido row

#### Scenario: Transition from terminal state
- **WHEN** avanzar_estado() is called on an order in CANCELADO or ENTREGADO state
- **THEN** the system raises HTTP 409 "Estado terminal — no se permiten más transiciones"

#### Scenario: PENDIENTE→CONFIRMADO blocked for CLIENT role
- **WHEN** a CLIENT role tries to call avanzar_estado() to set estado=CONFIRMADO
- **THEN** the service raises HTTP 403 "Solo el sistema puede confirmar pedidos"
  (enforcement note: role check occurs at router layer, documented here for completeness)

### Requirement: Append-only historial audit trail
The system SHALL maintain an immutable audit trail in historial_estado_pedido.
The HistorialEstadoPedidoRepository SHALL expose ONLY an append() method.
No UPDATE or DELETE operations SHALL be allowed on this table.

#### Scenario: Historial row written at creation
- **WHEN** a new Pedido is created
- **THEN** one HistorialEstadoPedido row is inserted with estado_anterior_id=NULL,
  estado_nuevo_id=1, and usuario_responsable_id=creator's user ID

#### Scenario: Historial row written at every state transition
- **WHEN** avanzar_estado() or cancelar() successfully changes order state
- **THEN** one HistorialEstadoPedido row is inserted with estado_anterior_id=previous_state,
  estado_nuevo_id=new_state, and usuario_responsable_id=the user performing the action

#### Scenario: Historial is immutable
- **WHEN** any code path attempts to UPDATE or DELETE a HistorialEstadoPedido row
- **THEN** the operation SHALL fail — HistorialEstadoPedidoRepository does not expose
  update() or delete() methods (enforced at repository interface level)

### Requirement: Price and address snapshot immutability
The system SHALL capture snapshots at order creation time. After creation, these values
SHALL NOT change even if the product price or delivery address is later modified.

#### Scenario: Price snapshot captured
- **WHEN** an order is created
- **THEN** each DetallePedido.precio_snapshot equals Producto.precio_base at the moment of
  creation, and Pedido.total equals the sum of (precio_snapshot * cantidad) for all detalles

#### Scenario: Address snapshot captured
- **WHEN** an order is created
- **THEN** Pedido.direccion_snapshot contains a JSON string with alias, linea1, ciudad,
  and codigo_postal fields from the DireccionEntrega at the moment of creation

### Requirement: Order creation rate limiting
The system SHALL enforce a maximum of 10 order creations per usuario per hour (US-073).

#### Scenario: Rate limit not exceeded
- **WHEN** a user submits fewer than 10 order creation requests within one hour
- **THEN** each request is processed normally

#### Scenario: Rate limit exceeded
- **WHEN** a user submits more than 10 order creation requests within one hour
- **THEN** the system returns HTTP 429 with Retry-After header

### Requirement: Order retrieval by user
The system SHALL allow a CLIENT to retrieve their own orders. An ADMIN or PEDIDOS role
SHALL be able to retrieve any order.

#### Scenario: Client retrieves own orders
- **WHEN** a CLIENT calls list_by_usuario() with their own usuario_id
- **THEN** the system returns all non-deleted orders for that user, ordered by creado_en DESC

#### Scenario: Unauthorized access to another user's order
- **WHEN** a CLIENT calls get_by_id_with_details() with a pedido_id belonging to a different user
- **THEN** the system raises HTTP 403
