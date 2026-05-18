## ADDED Requirements

### Requirement: El sistema valida la firma del webhook de MercadoPago antes de procesar (RN-PA06)
El sistema SHALL verificar la firma HMAC-SHA256 del header `x-signature` antes de procesar cualquier payload de webhook. Si la firma es inválida, el sistema SHALL registrar el intento en `pago_webhook_log` con `procesado=False` y retornar HTTP 400. En entorno `development` (ENV=development) con header ausente, el sistema SHALL loguear un warning y continuar. En entorno `production`, la ausencia del header SHALL resultar en HTTP 400.

#### Scenario: Webhook con firma válida es procesado
- **WHEN** MercadoPago envía `POST /api/v1/webhooks/mercadopago` con header `x-signature` válido y payload JSON
- **THEN** el sistema verifica la firma, la acepta y procesa el webhook

#### Scenario: Webhook con firma inválida es rechazado
- **WHEN** llega un request a `POST /api/v1/webhooks/mercadopago` con header `x-signature` cuya firma no coincide con el HMAC esperado
- **THEN** el sistema inserta un registro en `pago_webhook_log` con `procesado=False, error_msg="Firma inválida"` y retorna HTTP 400

#### Scenario: Webhook sin firma en entorno development continúa con warning
- **WHEN** llega un request a `POST /api/v1/webhooks/mercadopago` sin header `x-signature` y `ENV=development`
- **THEN** el sistema loguea un warning pero continúa procesando el webhook

### Requirement: Procesamiento idempotente de webhooks de pago aprobado
El sistema SHALL consultar el estado real del pago en la API de MP usando el `payment_id` del webhook. Si el pago está `approved`, el sistema SHALL actualizar `Pago.estado = "approved"` y ejecutar la transición FSM `PENDIENTE → CONFIRMADO` en el pedido asociado, todo en una única transacción UoW. Si ya existe un `Pago` con ese `mercadopago_id` y el mismo estado, el sistema SHALL retornar HTTP 200 sin modificar ningún dato.

#### Scenario: Webhook approved actualiza pago y confirma pedido
- **WHEN** llega un webhook de MP con `topic=payment` y el estado consultado en la API de MP es `approved`
- **THEN** el sistema actualiza `Pago.estado = "approved"`, ejecuta `PENDIENTE → CONFIRMADO` en el pedido, inserta en `pago_webhook_log` con `procesado=True` y retorna HTTP 200

#### Scenario: Webhook duplicado (mismo mercadopago_id y mismo estado) retorna 200 sin cambios
- **WHEN** llega un segundo webhook de MP con el mismo `payment_id` y el mismo estado que ya fue procesado
- **THEN** el sistema detecta que el `mercadopago_id` ya existe con ese estado en `pagos`, retorna HTTP 200 sin modificar ningún dato

#### Scenario: Webhook rejected actualiza solo el estado del pago sin cambiar el pedido
- **WHEN** llega un webhook de MP con estado `rejected`
- **THEN** el sistema actualiza `Pago.estado = "rejected"` y NO modifica el estado del pedido (permanece PENDIENTE), retorna HTTP 200

#### Scenario: Webhook con payment_id inexistente en MP API retorna 200 con log de error
- **WHEN** llega un webhook cuyo `payment_id` no se puede consultar en la API de MP (timeout o 404)
- **THEN** el sistema inserta en `pago_webhook_log` con `procesado=False, error_msg=<descripción del error>` y retorna HTTP 200 (para evitar reintentos infinitos de MP)

### Requirement: El endpoint webhook siempre retorna 200 para errores de procesamiento internos
El sistema SHALL retornar HTTP 200 ante cualquier error de procesamiento interno (BD no disponible, pedido no encontrado, error de SDK) para evitar que MercadoPago reintente indefinidamente. La excepción es la firma inválida (HTTP 400).

#### Scenario: Error de BD durante procesamiento retorna 200 con log
- **WHEN** ocurre un error de BD durante la actualización del Pago o la transición FSM del Pedido
- **THEN** el sistema loguea el error en `pago_webhook_log` con `procesado=False` y retorna HTTP 200
