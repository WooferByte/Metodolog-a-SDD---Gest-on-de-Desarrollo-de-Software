## Context

El sistema tiene pedidos funcionando con FSM de 6 estados (PENDIENTE→CONFIRMADO→EN_PREPARACIÓN→EN_CAMINO→ENTREGADO, con CANCELADO como terminal). La tabla `pagos` ya existe en el schema (migración 001) con columnas `id`, `pedido_id`, `mercadopago_id`, `estado`, `monto`, `creado_en`, `actualizado_en`. Falta: columna `preference_id` en `pagos` y la tabla `pago_webhook_log`.

El SDK `mercadopago ^2.2.0` está instalado. La variable de entorno es `MP_ACCESS_TOKEN`. El flujo FSM documenta que `1→2 (System only)` — la transición PENDIENTE→CONFIRMADO solo puede ser disparada por el sistema, no por usuarios.

La arquitectura sigue estrictamente: Router → Service → UoW → Repository → Model. El UoW en `backend/infrastructure/uow.py` expone repos por nombre (e.g., `uow.pedidos`). `BaseRepository[T]` en `backend/core/` provee operaciones CRUD base.

## Goals / Non-Goals

**Goals:**
- Crear preferencia de pago en MP Sandbox y persistir en BD atomicamente.
- Procesar webhooks de MP con validación de firma, idempotencia y actualización transaccional de Pago + FSM de Pedido.
- Exponer consulta de estado de pago con control de acceso (owner o admin).
- Audit trail completo de webhooks en `pago_webhook_log`.
- Tests unitarios con mock del SDK de MP.

**Non-Goals:**
- UI de checkout (será change separado `frontend-checkout-payment`).
- Soporte para múltiples métodos de pago o múltiples PSP.
- Reembolsos o devoluciones (fuera del alcance de este change).
- Producción (solo Sandbox en este change).
- Notificaciones push al usuario (fuera de alcance).

## Decisions

### D-1: Módulo `pagos/` como módulo independiente (no dentro de `pedidos/`)

**Decisión**: Crear `backend/pagos/` como módulo propio.

**Alternativa considerada**: Agregar endpoints de pago dentro de `pedidos/router.py` y `pedidos/service.py`.

**Razón**: Separación de concerns clara. El módulo `pedidos/` ya es complejo (FSM, snapshots, stock). Los pagos tienen su propio ciclo de vida, sus propios modelos y su propio repositorio. La dependencia es unidireccional: `pagos/service.py` importa de `pedidos/service.py` para disparar la transición FSM, no al revés.

---

### D-2: Validación de firma MP via header `x-signature` (RN-PA06)

**Decisión**: Implementar validación HMAC-SHA256 del header `x-signature` antes de procesar cualquier payload de webhook.

**Alternativa considerada**: Confiar en IP allowlist de MP.

**Razón**: La spec del proyecto (RN-PA06) lo requiere explícitamente. IP allowlist no es suficiente en sandbox y es frágil en producción. La clave de validación es `MP_ACCESS_TOKEN` (el SDK lo maneja internamente con `SDKManager.get_instance().get_secret_key()`).

**Implementación**: Extraer `ts` y `v1` del header `x-signature`, reconstruir el manifest `id:${payment_id};request-id:${request_id};ts:${ts};`, computar HMAC-SHA256, comparar con `v1`. Si falla: loguear en `pago_webhook_log` con `procesado=False`, retornar 400.

---

### D-3: Idempotencia basada en `mercadopago_id` UNIQUE en tabla `pagos`

**Decisión**: La columna `mercadopago_id` tiene constraint UNIQUE en la tabla `pagos`. El service verifica si ya existe un pago con ese `mercadopago_id` antes de procesar.

**Alternativa considerada**: Tabla separada de eventos procesados.

**Razón**: La tabla `pagos` ya tiene `mercadopago_id`. Agregar UNIQUE es la forma más simple y atómica. Si el webhook ya fue procesado con el mismo estado → return 200 sin cambios. Si llegó con estado diferente → procesar como actualización (e.g., `approved` sobre `pending`).

---

### D-4: Transición FSM PENDIENTE→CONFIRMADO desde `pagos/service.py`

**Decisión**: `pagos/service.py` importa `avanzar_estado` de `pedidos/service.py` y la ejecuta dentro del mismo UoW context para actualizar el pedido cuando `estado == "approved"`.

**Alternativa considerada**: Event bus interno (publish/subscribe).

**Razón**: El proyecto no tiene event bus. La llamada directa es simple, testeable y mantiene la atomicidad ACID dentro del mismo UoW. Solo se activa para `estado == "approved"` (webhook de pago aprobado). La transición `1→2` en el FSM ya está marcada como "System only" en `pedidos/service.py`.

---

### D-5: `pago_webhook_log` como tabla de audit trail inmutable

**Decisión**: Insertar SIEMPRE en `pago_webhook_log` al recibir un webhook, independientemente del resultado del procesamiento.

**Alternativa considerada**: Solo loguear errores.

**Razón**: Audit trail completo para debugging, compliance y replay manual de webhooks fallidos. El campo `procesado` (bool) + `error_msg` (nullable) distingue éxito de fallo sin perder el registro. El campo `payload` es JSONB para preservar el payload raw.

---

### D-6: Rate limiting solo en `crear-preferencia`, no en webhook

**Decisión**: Aplicar `@limiter.limit("5/minute")` en `POST /api/v1/pagos/crear-preferencia`. El webhook `POST /api/v1/webhooks/mercadopago` no tiene rate limiting.

**Razón**: El webhook es llamado por MercadoPago (servidor externo), no por usuarios. Rate limiting en el webhook causaría que MP deje de reintentar y los pagos queden en estado inconsistente. El endpoint de preferencia sí es llamado por clientes y debe protegerse contra abuso.

---

### D-7: Estructura del endpoint webhook — respuesta siempre 200

**Decisión**: El endpoint `POST /api/v1/webhooks/mercadopago` retorna 200 en todos los casos excepto firma inválida (400).

**Razón**: MercadoPago reintenta el webhook si recibe cualquier respuesta != 200. Para errores de procesamiento internos (e.g., pedido no encontrado, error de BD transitorio), es mejor retornar 200 y loguear el error en `pago_webhook_log` que causar reintentos infinitos. La excepción es firma inválida (400) porque indica un request malicioso que no debe ser procesado.

---

### D-8: El SDK de MP se inicializa en `core/config.py` y se inyecta via `Depends`

**Decisión**: El SDK (`mercadopago.SDK`) se inicializa una sola vez usando `MP_ACCESS_TOKEN` de `Settings`. Se expone como dependencia FastAPI en `core/dependencies.py`.

**Alternativa considerada**: Inicializar el SDK dentro de cada función de service.

**Razón**: Sigue el patrón de inyección de dependencias ya establecido en el proyecto. Facilita el mock en tests (se puede overridear la dependencia con un SDK mock).

## Risks / Trade-offs

- **Race condition en webhook concurrente**: Dos webhooks del mismo `mercadopago_id` llegan simultáneamente. El constraint UNIQUE en `mercadopago_id` actúa como lock implícito — el segundo INSERT fallará con IntegrityError, que el service captura y retorna 200. → **Mitigación**: Try/except `IntegrityError` en `PagoRepository.create()`.

- **MP cambia su formato de webhook**: El payload de MP puede variar entre versiones de API. → **Mitigación**: Almacenar el payload raw en `pago_webhook_log.payload` (JSONB) y consultar el estado real via `sdk.payment().get(payment_id)` en lugar de confiar solo en el payload del webhook.

- **Timeout en llamada al SDK de MP**: La llamada `sdk.payment().get(payment_id)` puede fallar si MP está degradado. → **Mitigación**: Try/except alrededor de llamadas SDK; si falla, loguear en `pago_webhook_log` con `error_msg` y retornar 200 (MP reintentará).

- **`preference_id` en tabla `pagos`**: La migración 001 creó `pagos` sin `preference_id`. La migración 010 agrega esta columna con `ALTER TABLE pagos ADD COLUMN IF NOT EXISTS preference_id VARCHAR`. → **Trade-off**: `IF NOT EXISTS` hace la migración idempotente pero puede ocultar inconsistencias de schema. Aceptable en este stage del proyecto.

- **Test de race condition**: Simular concurrencia en pytest es complejo. → **Mitigación**: Test con mock de `IntegrityError` en el repositorio, no con threads reales.

## Migration Plan

1. Implementar módulo `backend/pagos/` (model, schemas, repository, service, router).
2. Registrar `pagos_router` en `backend/main.py` bajo prefix `/api/v1`.
3. Registrar `webhooks_router` en `backend/main.py` bajo prefix `/api/v1`.
4. Crear migración `010_pagos_webhook_log.py`:
   - `ALTER TABLE pagos ADD COLUMN IF NOT EXISTS preference_id VARCHAR`
   - `CREATE TABLE pago_webhook_log (...)`
   - Índices: `pago_webhook_log(mercadopago_id)`, `pago_webhook_log(creado_en)`
5. Ejecutar `alembic upgrade head`.
6. Agregar `uow.pagos` y `uow.pago_webhook_logs` al `UnitOfWork`.
7. Escribir y ejecutar tests.

**Rollback**: `alembic downgrade -1`. La tabla `pago_webhook_log` y la columna `preference_id` se eliminan. Los endpoints desaparecen al eliminar los routers de `main.py`.

## Open Questions

- **Verificación de firma MP en Sandbox**: En modo Sandbox, MP puede no enviar siempre el header `x-signature`. Decisión: si el header está ausente en sandbox (ENV=development), loguear warning pero continuar. En producción (ENV=production), firma ausente = 400.
- **Monto a guardar en `Pago`**: ¿Usar el `total` del Pedido o el monto confirmado por MP? → Usar `total_pedido` del Pedido al crear la preferencia (antes del pago), y actualizar con el monto de MP al recibir el webhook `approved`.
