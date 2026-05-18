## 0. Skills

- [ ] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — arquitectura Router→Service→UoW→Repository→Model, Pydantic v2, FastAPI Depends
- [ ] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — diseño de índices, queries parametrizadas, JSONB, migraciones Alembic
- [ ] 0.3 Leer `.agents/skills/api-design/SKILL.md` — status codes, rate limiting, RFC 7807, response_model explícito
- [ ] 0.4 Leer `.agents/skills/rest-api-design-patterns/SKILL.md` — nomenclatura de endpoints, idempotencia, versionado
- [ ] 0.5 Leer `.agents/skills/jwt-security/SKILL.md` — validación de JWT, require_role, get_current_user
- [ ] 0.6 Leer `.agents/skills/web-payments/SKILL.md` — webhooks, validación de firma, idempotencia, SDK de pagos
- [ ] 0.7 Leer `.agents/skills/post-change-verification/SKILL.md` — criterios de aprobación: pytest ≥60% cov, alembic head, uvicorn arranca

## 1. Exploración de contexto existente

- [ ] 1.1 Leer `backend/infrastructure/uow.py` completo — entender cómo se exponen repos (uow.pedidos, uow.productos, etc.) y cómo agregar uow.pagos y uow.pago_webhook_logs
- [ ] 1.2 Leer `backend/core/` — identificar `BaseRepository[T]`, `Settings`, `dependencies.py` para entender el patrón de inyección de dependencias
- [ ] 1.3 Leer `backend/pedidos/service.py` completo — entender `avanzar_estado()`, `VALID_TRANSITIONS`, `SYSTEM_ONLY_TARGETS` para implementar `confirmar_pedido_por_pago()`
- [ ] 1.4 Leer `backend/pedidos/model.py` y `backend/core/models.py` — confirmar estructura de Pedido (estado_id, usuario_id, total) y relaciones
- [ ] 1.5 Verificar que la tabla `pagos` existe en Alembic: buscar en `backend/alembic/versions/` la migración que crea `pagos` y confirmar columnas presentes (id, pedido_id, mercadopago_id, estado, monto, creado_en, actualizado_en)
- [ ] 1.6 Leer `backend/main.py` — entender cómo se registran los routers y el limiter de slowapi para replicar el patrón

## 2. Modelo de datos — backend/pagos/model.py

- [ ] 2.1 Crear `backend/pagos/__init__.py` (vacío)
- [ ] 2.2 Crear `backend/pagos/model.py` con `SQLModel` class `PagoWebhookLog` (tabla `pago_webhook_log`):
  - Campos: `id` (int PK auto), `mercadopago_id` (str, nullable, indexed), `topic` (str), `payload` (dict via sa_column JSON/JSONB), `procesado` (bool, default False), `error_msg` (str, nullable), `creado_en` (datetime, default utcnow)
  - NO agregar `Pago` model aquí si ya existe en `core/models.py` — verificar en tarea 1.4
- [ ] 2.3 Si `Pago` no existe en `core/models.py`, crearlo en `backend/pagos/model.py` con: `id`, `pedido_id` (FK pedidos.id), `mercadopago_id` (str UNIQUE nullable), `preference_id` (str nullable), `estado` (str default "pending"), `monto` (Decimal), `creado_en`, `actualizado_en`

## 3. Migración Alembic — 010_pagos_webhook_log.py

- [ ] 3.1 Crear `backend/alembic/versions/010_pagos_webhook_log.py` con `upgrade()`:
  - `ALTER TABLE pagos ADD COLUMN IF NOT EXISTS preference_id VARCHAR` (columna nueva en tabla existente)
  - `CREATE TABLE pago_webhook_log (id SERIAL PK, mercadopago_id VARCHAR, topic VARCHAR NOT NULL, payload JSONB NOT NULL, procesado BOOLEAN NOT NULL DEFAULT FALSE, error_msg TEXT, creado_en TIMESTAMP DEFAULT NOW())`
  - `CREATE INDEX idx_webhook_log_mp_id ON pago_webhook_log(mercadopago_id)`
  - `CREATE INDEX idx_webhook_log_created ON pago_webhook_log(creado_en)`
- [ ] 3.2 Implementar `downgrade()` que revierte: `DROP TABLE pago_webhook_log`, `ALTER TABLE pagos DROP COLUMN IF EXISTS preference_id`
- [ ] 3.3 Configurar correctamente `down_revision` apuntando al hash de la migración anterior (009 o la última existente en `alembic/versions/`)
- [ ] 3.4 Ejecutar `alembic upgrade head` y verificar que termina sin error

## 4. Schemas Pydantic — backend/pagos/schemas.py

- [ ] 4.1 Crear `backend/pagos/schemas.py` con:
  - `CrearPreferenciaRequest(BaseModel)`: `pedido_id: int`
  - `CrearPreferenciaResponse(BaseModel)`: `init_point: str`, `preference_id: str`, `pago_id: int`
  - `PagoStatusResponse(BaseModel)`: `pago_id: int`, `mercadopago_id: str | None`, `estado: str`, `monto: Decimal`, `creado_en: datetime`, `actualizado_en: datetime`
  - `WebhookMPPayload(BaseModel)`: `topic: str | None = None`, `id: str | None = None`, `data: dict | None = None` — usar `model_config = ConfigDict(extra='allow')` para tolerancia a campos extra de MP

## 5. Repositorios — backend/pagos/repository.py

- [ ] 5.1 Crear `backend/pagos/repository.py` con `PagoRepository(BaseRepository[Pago])`:
  - `get_by_pedido_id(pedido_id: int) -> Pago | None`
  - `get_by_mercadopago_id(mp_id: str) -> Pago | None`
  - Heredar `create()` y `update()` de BaseRepository
- [ ] 5.2 Agregar `PagoWebhookLogRepository(BaseRepository[PagoWebhookLog])` en el mismo archivo:
  - Solo `create()` — sin `update()` ni `delete()` (append-only per spec)
  - `get_by_mercadopago_id(mp_id: str) -> list[PagoWebhookLog]` para debugging

## 6. Actualización del UnitOfWork — backend/infrastructure/uow.py

- [ ] 6.1 Importar `PagoRepository` y `PagoWebhookLogRepository` en `uow.py`
- [ ] 6.2 Agregar `self.pagos = PagoRepository(session)` en `__aenter__` del UoW
- [ ] 6.3 Agregar `self.pago_webhook_logs = PagoWebhookLogRepository(session)` en `__aenter__` del UoW

## 7. Integración SDK MercadoPago — backend/core/

- [ ] 7.1 Agregar `MP_ACCESS_TOKEN: str` al modelo `Settings` en `backend/core/config.py` (con `Field(...)` sin default — falla si ausente)
- [ ] 7.2 Crear función `get_mp_sdk()` en `backend/core/dependencies.py` que retorna `mercadopago.SDK(settings.MP_ACCESS_TOKEN)`. Usar `@lru_cache` o inicialización en startup para no recrear el SDK en cada request.

## 8. Función de transición FSM en pedidos — backend/pedidos/service.py

- [ ] 8.1 Agregar función `confirmar_pedido_por_pago(pedido_id: int, uow: UnitOfWork) -> None` en `backend/pedidos/service.py`:
  - Obtener pedido por id; si no existe → `HTTPException(404)`
  - Verificar que `pedido.estado_id == 1` (PENDIENTE); si no → `HTTPException(409)`
  - Crear `HistorialEstadoPedido(pedido_id, estado_id=2, cambiado_por=None)` (sistema)
  - Actualizar `pedido.estado_id = 2`
  - NO llamar `session.commit()` — el UoW lo maneja

## 9. Service de pagos — backend/pagos/service.py

- [ ] 9.1 Crear `backend/pagos/service.py` con función `crear_preferencia(pedido_id, usuario_id, sdk, uow)`:
  - Buscar pedido; 404 si no existe; 403 si `pedido.usuario_id != usuario_id`; 409 si `pedido.estado_id != 1`
  - Llamar `sdk.preference().create({"items": [...], "back_urls": {...}, "notification_url": "..."})` con datos del pedido
  - Crear `Pago(pedido_id, preference_id, estado="pending", monto=pedido.total)` via `uow.pagos.create()`
  - Retornar `CrearPreferenciaResponse(init_point, preference_id, pago_id)`
- [ ] 9.2 Agregar función `procesar_webhook(payload_raw: dict, signature: str | None, request_id: str | None, sdk, uow)`:
  - Insertar en `pago_webhook_log` inmediatamente (antes de procesar) con `procesado=False`
  - Validar firma: extraer `ts` y `v1` de `signature`, reconstruir manifest, comparar HMAC-SHA256 con `MP_ACCESS_TOKEN`. Si falla en producción → raise `HTTPException(400)`. Si ENV=development y sin header → warning y continuar.
  - Extraer `payment_id` del payload (campo `data.id` o `id`)
  - Consultar `sdk.payment().get(payment_id)` para obtener estado real
  - Si estado `approved`: buscar/crear Pago, actualizar estado, llamar `confirmar_pedido_por_pago`
  - Si estado `rejected`/`cancelled`: actualizar solo `Pago.estado` sin tocar el pedido
  - Actualizar log con `procesado=True`; en caso de excepción capturar, actualizar log con `error_msg`, retornar sin reraise
- [ ] 9.3 Agregar función `get_pago_status(pedido_id: int, usuario_id: int, rol: str, uow)`:
  - Buscar pedido; 404 si no existe
  - Si `rol != "ADMIN"` y `pedido.usuario_id != usuario_id` → 403
  - Buscar Pago por `pedido_id`; 404 si no existe
  - Retornar `PagoStatusResponse`

## 10. Router — backend/pagos/router.py

- [ ] 10.1 Crear `backend/pagos/router.py` con `pagos_router = APIRouter(prefix="/pagos", tags=["pagos"])`:
  - `POST /crear-preferencia` con `response_model=CrearPreferenciaResponse`, `@limiter.limit("5/minute")`, `Depends(require_role(["CLIENT"]))`, `Depends(get_current_user)`
- [ ] 10.2 Crear `webhooks_router = APIRouter(prefix="/webhooks", tags=["webhooks"])` (puede estar en el mismo archivo o en `backend/pagos/webhook_router.py`):
  - `POST /mercadopago` con `response_model` simple `{"status": "ok"}`, SIN autenticación JWT, SIN rate limiting
- [ ] 10.3 Agregar `GET /pagos/{pedido_id}/status` en `pagos_router` con `response_model=PagoStatusResponse`, `Depends(require_role(["CLIENT", "ADMIN"]))`, `Depends(get_current_user)`
- [ ] 10.4 Todos los endpoints deben tener `response_model` explícito (checklist pre-commit)

## 11. Registro de routers en main.py

- [ ] 11.1 Importar `pagos_router` y `webhooks_router` en `backend/main.py`
- [ ] 11.2 Registrar `app.include_router(pagos_router, prefix="/api/v1")`
- [ ] 11.3 Registrar `app.include_router(webhooks_router, prefix="/api/v1")`

## 12. Tests — backend/tests/test_pagos.py

- [ ] 12.1 Crear `backend/tests/test_pagos.py` con fixture que mockea `mercadopago.SDK` usando `unittest.mock.patch`
- [ ] 12.2 Test: `test_crear_preferencia_exitosa` — mock SDK.preference().create() retorna `{"init_point": "https://mp.com/...", "id": "pref_123"}`, verificar que se crea Pago en BD y respuesta 201
- [ ] 12.3 Test: `test_crear_preferencia_pedido_ajeno` — verificar HTTP 403
- [ ] 12.4 Test: `test_crear_preferencia_pedido_no_pendiente` — pedido en CONFIRMADO, verificar HTTP 409
- [ ] 12.5 Test: `test_webhook_approved_actualiza_pago_y_pedido` — mock SDK.payment().get() retorna `{"status": "approved", "transaction_amount": 150.0}`, verificar que Pago.estado="approved" y Pedido.estado_id=2
- [ ] 12.6 Test: `test_webhook_firma_invalida` — enviar webhook sin header `x-signature` válido en ENV=production, verificar HTTP 400
- [ ] 12.7 Test: `test_webhook_idempotente` — enviar mismo webhook dos veces, verificar que segunda llamada retorna 200 sin duplicar datos
- [ ] 12.8 Test: `test_webhook_race_condition` — mock `PagoRepository.create()` lanzando `IntegrityError` (simula concurrencia), verificar que retorna 200 sin excepción no manejada
- [ ] 12.9 Test: `test_get_pago_status_exitoso` — CLIENT obtiene status de su propio pago
- [ ] 12.10 Test: `test_get_pago_status_ajeno_forbiden` — CLIENT intenta obtener status de pago de otro usuario, verificar 403

## 13. Verificación post-implementación (post-change-verification)

- [ ] 13.1 Ejecutar `cd backend && .venv/Scripts/pytest --cov=. --cov-report=term-missing -x -q` — verificar ≥60% coverage backend
- [ ] 13.2 Ejecutar `.venv/Scripts/alembic upgrade head` — verificar que termina sin error y muestra migración 010 aplicada
- [ ] 13.3 Ejecutar `.venv/Scripts/alembic current` — verificar que muestra el hash de 010 con `(head)`
- [ ] 13.4 Ejecutar `.venv/Scripts/black --check .` y `.venv/Scripts/flake8 .` — verificar lint limpio
- [ ] 13.5 Levantar `uvicorn main:app --reload` y verificar que Swagger muestra los 3 nuevos endpoints bajo `/api/v1/pagos` y `/api/v1/webhooks`
- [ ] 13.6 Verificar en Swagger que `POST /api/v1/pagos/crear-preferencia` requiere Bearer token (candado en la UI)
- [ ] 13.7 Verificar que `POST /api/v1/webhooks/mercadopago` NO tiene candado (endpoint público)
