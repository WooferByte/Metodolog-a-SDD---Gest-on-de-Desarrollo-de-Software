## 0. Skills

- [ ] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — endpoints FastAPI, DDD, arquitectura Router→Service→UoW→Repository
- [ ] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — optimización queries, índices, count con filtros
- [ ] 0.3 Leer `.agents/skills/api-design/SKILL.md` — status codes, paginación, rate limiting, RFC 7807
- [ ] 0.4 Leer `.agents/skills/rest-api-design-patterns/SKILL.md` — resource naming, ownership checks, colecciones paginadas
- [ ] 0.5 Leer `.agents/skills/jwt-security/SKILL.md` — validación JWT, `require_role()`, dependency injection
- [ ] 0.6 Leer `.agents/skills/post-change-verification/SKILL.md` — checklist de verificación post-implementación

## 1. Verificación del estado actual

- [ ] 1.1 Leer `backend/pedidos/service.py` completo — confirmar que `create_pedido()`, `avanzar_estado()`, `cancelar()` existen y sus firmas
- [ ] 1.2 Leer `backend/pedidos/schemas.py` — confirmar schemas: `PedidoCreate`, `PedidoResponse`, `PedidoDetailResponse`, `AvanzarEstadoRequest`
- [ ] 1.3 Leer `backend/pedidos/repository.py` — confirmar métodos: `create_with_details`, `get_by_id_with_details`, `list_by_usuario`, `update_estado`
- [ ] 1.4 Leer `backend/pedidos/router.py` — confirmar que solo tiene `/validar` y verificar imports existentes
- [ ] 1.5 Leer `backend/infrastructure/uow.py` — confirmar que `uow.pedidos` y `uow.historial_estado_pedido` están expuestos
- [ ] 1.6 Leer `backend/core/limiter.py` — confirmar instancia `limiter` disponible
- [ ] 1.7 Leer `backend/core/dependencies.py` — confirmar `require_role()` y `get_current_user()` disponibles

## 2. Schema: PaginatedPedidosResponse

- [ ] 2.1 Agregar `PaginatedPedidosResponse` en `backend/pedidos/schemas.py` con campos: `items: list[PedidoResponse]`, `total: int`, `limit: int`, `offset: int`
- [ ] 2.2 Verificar que `PedidoResponse` y `PedidoDetailResponse` tienen `model_config = {"from_attributes": True}` (ya deben tenerlo)

## 3. Repository: count_by_usuario

- [ ] 3.1 Agregar método `count_by_usuario(self, usuario_id: int) -> int` en `PedidoRepository` (`backend/pedidos/repository.py`)
- [ ] 3.2 Implementar con `SELECT COUNT(*) FROM pedidos WHERE usuario_id = :id AND eliminado_en IS NULL` usando SQLAlchemy ORM (no concatenación SQL)

## 4. Router: 5 endpoints REST

- [ ] 4.1 Agregar imports necesarios en `backend/pedidos/router.py`: `Request` de fastapi, `limiter` de `core.limiter`, schemas nuevos, servicio `service`
- [ ] 4.2 Implementar `POST /pedidos` con:
  - `require_role(["CLIENT"])` como dependency
  - `@limiter.limit("10/hour", key_func=lambda req: f"pedidos_create:{req.state.user_id if hasattr(req.state, 'user_id') else req.client.host}")` — O usar `request: Request` + `current_user.id` como key
  - Llamada a `service.create_pedido(request_body, current_user.id, uow)` dentro de `async with uow`
  - `response_model=PedidoResponse`, `status_code=201`
  - Header `Location` en la respuesta: `/api/v1/pedidos/{pedido.id}`
- [ ] 4.3 Implementar `GET /pedidos` con:
  - `require_role(["CLIENT"])` como dependency
  - Query params: `limit: int = Query(default=20, ge=1, le=100)` y `offset: int = Query(default=0, ge=0)`
  - Llamadas a `uow.pedidos.list_by_usuario(current_user.id, skip=offset, limit=limit)` y `uow.pedidos.count_by_usuario(current_user.id)` en el mismo `async with uow`
  - `response_model=PaginatedPedidosResponse`, `status_code=200`
- [ ] 4.4 Implementar `GET /pedidos/{pedido_id}` con:
  - `require_role(["CLIENT", "ADMIN"])` como dependency (cualquiera de los dos puede llamarlo, pero el ownership check diferencia)
  - Dentro de `async with uow`: llamar a `uow.pedidos.get_by_id_with_details(pedido_id)`
  - Si no existe → raise HTTPException 404 (RFC 7807)
  - Si current_user no es ADMIN y `pedido.usuario_id != current_user.id` → raise HTTPException 403 (RFC 7807)
  - Construir `PedidoDetailResponse` con el pedido y detalles
  - `response_model=PedidoDetailResponse`, `status_code=200`
- [ ] 4.5 Implementar `PATCH /pedidos/{pedido_id}/estado` con:
  - `require_role(["ADMIN"])` como dependency
  - Body: `AvanzarEstadoRequest` (ya existe en schemas)
  - Llamada a `service.avanzar_estado(pedido_id, request_body.nuevo_estado_id, current_user.id, uow, is_system=False)` dentro de `async with uow`
  - `response_model=PedidoResponse`, `status_code=200`
- [ ] 4.6 Implementar `DELETE /pedidos/{pedido_id}` con:
  - `require_role(["CLIENT", "ADMIN"])` como dependency
  - Dentro de `async with uow`:
    1. Buscar pedido con `uow.pedidos.get_by_id(pedido_id)`
    2. Si no existe → 404 (RFC 7807)
    3. Si CLIENT y `pedido.usuario_id != current_user.id` → 403 (RFC 7807)
    4. Si CLIENT y `pedido.estado_pedido_id != 1` (no PENDIENTE) → 409 (RFC 7807: "solo se puede cancelar en estado PENDIENTE")
    5. Llamar a `service.cancelar(pedido_id, current_user.id, uow)` — revierte stock y cambia estado FSM
    6. Setear `pedido_cancelado.eliminado_en = datetime.utcnow()` y `uow.session.add(pedido_cancelado)`
  - `response_model=PedidoResponse`, `status_code=200`

## 5. Rate limiting: configuración por usuario

- [ ] 5.1 Verificar que `app.state.limiter = limiter` está configurado en `backend/main.py`
- [ ] 5.2 Verificar que `RateLimitExceeded` exception handler está registrado en `main.py` y devuelve RFC 7807
- [ ] 5.3 En el endpoint `POST /pedidos`, usar `current_user.id` como clave de rate limiting (ver design D-01). Implementación sugerida: usar `key_func` en el decorator `@limiter.limit` que recibe el `Request` e inspecciona el token decodificado o usa una clave derivada del usuario autenticado
- [ ] 5.4 Documentar la key_func elegida en un comentario inline en el router

## 6. Tests de integración

- [ ] 6.1 Crear `backend/tests/test_orders_api.py` con estructura de clase `TestOrdersAPI`
- [ ] 6.2 Test `test_create_pedido_no_auth` → POST /pedidos sin token → 401
- [ ] 6.3 Test `test_create_pedido_forbidden_role` → POST /pedidos con token de ADMIN (sin CLIENT) → 403
- [ ] 6.4 Test `test_create_pedido_success` → POST /pedidos con CLIENT válido, items y dirección válidos → 201 con body PedidoResponse
- [ ] 6.5 Test `test_create_pedido_rate_limit` → POST /pedidos 11 veces en rápida sucesión → último request retorna 429
- [ ] 6.6 Test `test_create_pedido_wrong_address` → direccion_entrega_id de otro usuario → 403
- [ ] 6.7 Test `test_list_pedidos_isolation` → CLIENT-A hace GET /pedidos y no ve pedidos de CLIENT-B
- [ ] 6.8 Test `test_list_pedidos_pagination` → `?limit=1&offset=0` retorna exactamente 1 item y `total` correcto
- [ ] 6.9 Test `test_get_pedido_detail_own` → CLIENT accede al detalle de su pedido → 200 con detalles
- [ ] 6.10 Test `test_get_pedido_detail_other_user` → CLIENT-A intenta ver pedido de CLIENT-B → 403
- [ ] 6.11 Test `test_get_pedido_detail_admin` → ADMIN puede ver el pedido de cualquier usuario → 200
- [ ] 6.12 Test `test_get_pedido_not_found` → id inexistente → 404
- [ ] 6.13 Test `test_avanzar_estado_valid_transition` → ADMIN avanza pedido PENDIENTE→CONFIRMADO → 200
- [ ] 6.14 Test `test_avanzar_estado_invalid_fsm` → ADMIN intenta PENDIENTE→ENTREGADO → 409
- [ ] 6.15 Test `test_avanzar_estado_client_forbidden` → CLIENT intenta PATCH /estado → 403
- [ ] 6.16 Test `test_delete_pedido_pendiente_by_client` → CLIENT cancela su pedido PENDIENTE → 200, eliminado_en seteado
- [ ] 6.17 Test `test_delete_pedido_non_pendiente_by_client` → CLIENT intenta cancelar pedido CONFIRMADO → 409
- [ ] 6.18 Test `test_delete_pedido_other_user` → CLIENT-A intenta cancelar pedido de CLIENT-B → 403
- [ ] 6.19 Test `test_delete_soft_delete_removes_from_list` → pedido cancelado ya no aparece en GET /pedidos
- [ ] 6.20 Test `test_delete_pedido_admin_can_cancel_confirmed` → ADMIN cancela pedido CONFIRMADO → 200

## 7. Verificación post-implementación (post-change-verification)

- [ ] 7.1 Correr `backend/.venv/Scripts/black --check .` — sin errores de formato
- [ ] 7.2 Correr `backend/.venv/Scripts/flake8 .` — sin errores de lint
- [ ] 7.3 Correr `backend/.venv/Scripts/pytest --cov=. --cov-report=term-missing -x -q` — todos los tests pasan, coverage ≥ 60%
- [ ] 7.4 Verificar que el coverage de `pedidos/router.py` es ≥ 80% (nuevo código debe estar bien cubierto)
- [ ] 7.5 Arrancar `uvicorn main:app --reload` y verificar que `Application startup complete` aparece sin errores
- [ ] 7.6 Abrir `http://localhost:8000/docs` y confirmar que los 6 endpoints de `/pedidos` aparecen en Swagger (`/validar` + los 5 nuevos)
- [ ] 7.7 Test manual: autenticar como CLIENT y ejecutar flujo completo: crear pedido → ver listado → ver detalle → cancelar → confirmar que ya no aparece en listado

## 8. Checklist pre-commit

- [ ] 8.1 `response_model` explícito en los 5 nuevos endpoints
- [ ] 8.2 Ningún `session.commit()` en router ni service (UoW lo maneja)
- [ ] 8.3 Todos los errores en los nuevos endpoints usan RFC 7807
- [ ] 8.4 Rate limiting configurado en POST /pedidos con key por usuario_id
- [ ] 8.5 Soft delete con `eliminado_en` — no hay `DELETE FROM` en ningún archivo modificado
- [ ] 8.6 Tests usan pytest + pytest-asyncio (no jest, no unittest directo)
- [ ] 8.7 No hay `.env` o credenciales en el commit
