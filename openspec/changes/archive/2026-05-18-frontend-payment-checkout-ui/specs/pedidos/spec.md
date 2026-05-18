## MODIFIED Requirements

### Requirement: El checkout frontend crea el pedido antes de iniciar el pago
El flujo de checkout SHALL llamar a `POST /api/v1/pedidos` con los datos del carrito y del comprador ANTES de crear la preferencia de pago MercadoPago. Este requerimiento complementa la FSM del pedido existente en el backend.

#### Scenario: Creación del pedido desde el checkout con carrito activo
- **WHEN** el usuario confirma el pago con el formulario válido y el carrito tiene al menos 1 item
- **THEN** el sistema SHALL enviar `POST /api/v1/pedidos` con el contenido del carrito y recibir `{ id: pedido_id, estado: 'PENDIENTE' }` como respuesta

#### Scenario: El pedido_id se guarda en paymentStore para el flujo de pago
- **WHEN** `POST /api/v1/pedidos` retorna con éxito
- **THEN** `paymentStore.pedidoId` SHALL establecerse al `id` retornado por la API

#### Scenario: El pedido queda en estado PENDIENTE hasta confirmación de pago
- **WHEN** el pedido se crea exitosamente
- **THEN** el estado inicial del pedido en backend SHALL ser `PENDIENTE` y permanecerá en ese estado hasta que el webhook de MP confirme el pago o el usuario cancele
