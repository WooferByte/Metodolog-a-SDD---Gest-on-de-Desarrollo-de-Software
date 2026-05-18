## Why

El sistema de pedidos está completo pero no tiene mecanismo de pago real. Los clientes pueden crear pedidos pero no pueden pagarlos, bloqueando el flujo de negocio completo. Se integra MercadoPago Sandbox para habilitar el ciclo de pago end-to-end: preferencia → redirect MP → webhook de confirmación → actualización de estado del pedido.

## What Changes

- **Nuevo endpoint** `POST /api/v1/pagos/crear-preferencia`: recibe `pedido_id`, valida ownership, llama al SDK de MercadoPago, crea registro `Pago` en BD y devuelve `init_point` para redirigir al usuario.
- **Nuevo endpoint** `POST /api/v1/webhooks/mercadopago`: webhook público (sin auth JWT) que valida firma MP, consulta el estado real del pago en la API de MP, actualiza `Pago` y transiciona el estado del `Pedido` en la FSM, idempotente.
- **Nuevo endpoint** `GET /api/v1/pagos/{pedido_id}/status`: consulta de estado de pago para el cliente dueño del pedido o admin.
- **Nuevo modelo** `PagoWebhookLog`: tabla `pago_webhook_log` para audit trail de todos los webhooks recibidos (topic, payload JSONB, procesado, error_msg).
- **Nueva migración Alembic** `010_pagos_webhook_log`: crea `pago_webhook_log` e índices; agrega columna `preference_id` a `pagos` si no existe.
- **Módulo completo** `backend/pagos/`: model, schemas, repository, service, router siguiendo la arquitectura Router → Service → UoW → Repository → Model.
- **Tests** `backend/tests/test_pagos.py`: crear preferencia (mock SDK), procesar webhook válido/inválido, idempotencia, race condition.
- Rate limiting en `crear-preferencia`: 5 requests/minuto por usuario autenticado (slowapi).
- Validación de firma MP en webhook via header `x-signature` (RN-PA06).
- Transacciones atómicas: actualizar `Pago` + transición FSM del `Pedido` en la misma UoW.

## Capabilities

### New Capabilities

- `payment-preference-creation`: Creación de preferencia de pago en MercadoPago, vinculación con pedido y almacenamiento de `preference_id` + `init_point`.
- `payment-webhook-processing`: Recepción, validación de firma, procesamiento idempotente de webhooks de MercadoPago y actualización de estado del pedido vía FSM.
- `payment-status-query`: Consulta de estado actual de un pago asociado a un pedido (para cliente owner o admin).
- `payment-webhook-audit`: Registro inmutable de todos los webhooks recibidos en `pago_webhook_log` con payload JSONB y estado de procesamiento.

### Modified Capabilities

- `pedidos-fsm`: La FSM del pedido incorpora una nueva transición válida desde contexto sistema: `PENDIENTE → CONFIRMADO` disparada exclusivamente por el webhook de pago aprobado (no disponible para clientes ni stock managers).

## Impact

- **Backend**: nuevo módulo `backend/pagos/` (5 archivos), nueva migración `010_pagos_webhook_log.py`, nuevo test `test_pagos.py`.
- **Base de datos**: nueva tabla `pago_webhook_log`, columna `preference_id` en tabla `pagos` (ya existente desde migración 001).
- **Dependencias**: `mercadopago ^2.2.0` ya instalado en `backend/pyproject.toml`. No se requieren instalaciones adicionales.
- **Variables de entorno**: `MP_ACCESS_TOKEN` (ya en `.env.example`). No se agregan nuevas variables.
- **FSM de pedidos**: `pedidos/service.py` recibe nueva función de transición `PENDIENTE → CONFIRMADO` para ser llamada desde `pagos/service.py` vía UoW.
- **Sin cambios en frontend**: este change es 100% backend.
- **Seguridad**: endpoint webhook es público (sin JWT) pero protegido por validación de firma HMAC de MercadoPago.
