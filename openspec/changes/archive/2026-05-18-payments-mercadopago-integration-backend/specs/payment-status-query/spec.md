## ADDED Requirements

### Requirement: Cliente puede consultar el estado de su propio pago
El sistema SHALL permitir que un usuario autenticado con rol CLIENT consulte el estado del pago asociado a un pedido propio. El sistema SHALL retornar los campos `pago_id`, `mercadopago_id`, `estado`, `monto`, `creado_en`, `actualizado_en`.

#### Scenario: Cliente consulta estado de pago de su pedido exitosamente
- **WHEN** un CLIENT autenticado envía `GET /api/v1/pagos/{pedido_id}/status` con un `pedido_id` que le pertenece y tiene un Pago asociado
- **THEN** el sistema retorna HTTP 200 con `{ "pago_id": <id>, "mercadopago_id": "...", "estado": "approved"|"pending"|"rejected"|"cancelled"|"refunded", "monto": <decimal>, "creado_en": <datetime>, "actualizado_en": <datetime> }`

#### Scenario: Cliente recibe 404 si no hay pago para el pedido
- **WHEN** un CLIENT autenticado envía `GET /api/v1/pagos/{pedido_id}/status` para un pedido propio que aún no tiene Pago asociado
- **THEN** el sistema retorna HTTP 404 con RFC 7807 `{ "title": "Pago no encontrado", "detail": "No existe pago registrado para el pedido indicado." }`

#### Scenario: Cliente recibe 403 si intenta consultar pago de otro usuario
- **WHEN** un CLIENT autenticado envía `GET /api/v1/pagos/{pedido_id}/status` con un `pedido_id` que pertenece a otro usuario
- **THEN** el sistema retorna HTTP 403 con RFC 7807

### Requirement: ADMIN puede consultar el estado de pago de cualquier pedido
El sistema SHALL permitir que un usuario con rol ADMIN consulte el estado del pago de cualquier pedido, sin restricción de ownership.

#### Scenario: ADMIN consulta estado de pago de cualquier pedido
- **WHEN** un ADMIN autenticado envía `GET /api/v1/pagos/{pedido_id}/status` con cualquier `pedido_id` existente que tiene Pago
- **THEN** el sistema retorna HTTP 200 con los datos del pago
