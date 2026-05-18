## ADDED Requirements

### Requirement: Todo webhook recibido es registrado en pago_webhook_log antes de ser procesado
El sistema SHALL insertar un registro en `pago_webhook_log` para CADA webhook de MP recibido, independientemente del resultado del procesamiento. El registro SHALL incluir: `mercadopago_id`, `topic`, `payload` (JSONB raw), `procesado` (bool), `error_msg` (nullable), `creado_en`.

#### Scenario: Webhook procesado exitosamente genera log con procesado=True
- **WHEN** un webhook de MP es recibido, validado y procesado exitosamente
- **THEN** se inserta en `pago_webhook_log` con `procesado=True, error_msg=NULL`

#### Scenario: Webhook con error de procesamiento genera log con procesado=False
- **WHEN** un webhook de MP es recibido pero falla durante el procesamiento (firma inválida, error de BD, pedido no encontrado)
- **THEN** se inserta en `pago_webhook_log` con `procesado=False, error_msg=<descripción del error>`

#### Scenario: El log preserva el payload raw del webhook
- **WHEN** se inserta un registro en `pago_webhook_log`
- **THEN** el campo `payload` contiene el JSON completo del body del request de MP, sin modificaciones

### Requirement: La tabla pago_webhook_log es append-only (solo INSERT, nunca UPDATE ni DELETE)
El sistema SHALL solo insertar registros en `pago_webhook_log`. No se SHALL realizar UPDATE ni DELETE sobre esta tabla. Toda corrección se hace insertando un nuevo registro.

#### Scenario: Intento de modificar un log existente es bloqueado a nivel de servicio
- **WHEN** el service intenta modificar un registro de `pago_webhook_log`
- **THEN** no existe método `update` en `PagoWebhookLogRepository` — solo `create` y queries de lectura

### Requirement: Índices para consulta eficiente de pago_webhook_log
El sistema SHALL crear índices en `pago_webhook_log(mercadopago_id)` y `pago_webhook_log(creado_en)` para soportar búsquedas por ID de pago MP y rangos temporales.

#### Scenario: Consulta por mercadopago_id es eficiente
- **WHEN** se consulta `pago_webhook_log` filtrando por `mercadopago_id`
- **THEN** la query usa el índice `idx_webhook_log_mp_id` y no hace full table scan
