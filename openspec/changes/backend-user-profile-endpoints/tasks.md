# Tasks: backend-user-profile-endpoints

## 0. Skills

- [ ] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — arquitectura Router→Service→UoW→Repository, convenciones FastAPI DDD [skill: python-fastapi-ddd-skill]
- [ ] 0.2 Leer `.agents/skills/api-design/SKILL.md` — status codes, response_model explícito, RFC 7807, formato de errores 4xx [skill: api-design]
- [ ] 0.3 Leer `.agents/skills/jwt-security/SKILL.md` — validación JWT, uso de get_current_user(), revocación de refresh tokens (RN-AU04) [skill: jwt-security]

---

## 1. Schemas — `backend/usuarios/perfil_schemas.py` (NUEVO)

- [ ] 1.1 Crear `backend/usuarios/perfil_schemas.py` con clase `PerfilUpdate` — campos opcionales `nombre` (min=1, max=100, sanitizado con `sanitize_text`) y `telefono` (max=20); `model_validator(mode="after")` que lanza `ValueError` si ambos son `None` [skill: python-fastapi-ddd-skill, api-design]
- [ ] 1.2 Agregar clase `CambiarPasswordRequest` en el mismo archivo — campos `password_actual` y `nueva_password` (ambos min=8, max=128); `model_validator(mode="after")` que lanza `ValueError` si `nueva_password == password_actual` [skill: api-design, jwt-security]
- [ ] 1.3 Verificar que `UsuarioResponse` en `backend/usuarios/schemas.py` incluye `telefono` y `apellido` como `Optional[str]` — NO modificar si ya está correcto [skill: python-fastapi-ddd-skill]

## 2. Service — `backend/usuarios/perfil_service.py` (NUEVO)

- [ ] 2.1 Crear `backend/usuarios/perfil_service.py` con función `get_perfil(current_user: Usuario) -> UsuarioResponse` — retorna `UsuarioResponse.model_validate(current_user)` sin acceso a BD [skill: python-fastapi-ddd-skill]
- [ ] 2.2 Implementar `update_perfil(current_user: Usuario, data: PerfilUpdate, uow: UnitOfWork) -> UsuarioResponse` — parchear solo los campos no-`None` de `data` sobre `current_user`, llamar `await uow.usuarios.update(current_user)`, retornar `UsuarioResponse.model_validate(current_user)`. El service NUNCA llama `session.commit()` — el UoW lo maneja. [skill: python-fastapi-ddd-skill]
- [ ] 2.3 Implementar `cambiar_password(current_user: Usuario, data: CambiarPasswordRequest, uow: UnitOfWork) -> None`:
  - Llamar `verify_password(data.password_actual, current_user.hashed_password)` — si False, lanzar `HTTPException(status_code=400, detail={RFC7807 "Contraseña actual incorrecta"})` [skill: jwt-security]
  - Llamar `hash_password(data.nueva_password)` (importar de `core.security`) y asignar a `current_user.hashed_password` [skill: jwt-security]
  - Llamar `await uow.usuarios.update(current_user)` [skill: python-fastapi-ddd-skill]
  - Obtener todos los refresh tokens del usuario: `tokens = await uow.refresh_tokens.find_all_by(usuario_id=current_user.id)` [skill: jwt-security]
  - Para cada token donde `token.revoked_at is None`: asignar `token.revoked_at = datetime.utcnow()` y llamar `await uow.refresh_tokens.update(token)` — RN-AU04 complied [skill: jwt-security]
  - Retornar `None` (204 No Content)

## 3. Router — `backend/usuarios/perfil_router.py` (NUEVO)

- [ ] 3.1 Crear `backend/usuarios/perfil_router.py` con `APIRouter(prefix="/perfil", tags=["Perfil"])` [skill: python-fastapi-ddd-skill, api-design]
- [ ] 3.2 Implementar `GET ""` (`/api/v1/perfil`):
  - `response_model=UsuarioResponse`, `status_code=200`
  - Dependency: `current_user: Usuario = Depends(get_current_user)`
  - Sin UoW (lectura pura desde dependency)
  - Delega a `perfil_service.get_perfil(current_user)` [skill: api-design]
- [ ] 3.3 Implementar `PUT ""` (`/api/v1/perfil`):
  - `response_model=UsuarioResponse`, `status_code=200`
  - Body: `data: PerfilUpdate`
  - Dependencies: `current_user`, `uow: UnitOfWork = Depends(get_uow)`
  - Patrón `async with uow:` — igual que `auth/router.py`
  - Delega a `perfil_service.update_perfil(current_user, data, uow)` [skill: python-fastapi-ddd-skill, api-design]
- [ ] 3.4 Implementar `POST "/cambiar-password"` (`/api/v1/perfil/cambiar-password`):
  - `response_model=None`, `status_code=204`
  - Body: `data: CambiarPasswordRequest`
  - Dependencies: `current_user`, `uow: UnitOfWork = Depends(get_uow)`
  - Patrón `async with uow:`
  - Delega a `perfil_service.cambiar_password(current_user, data, uow)` [skill: python-fastapi-ddd-skill, api-design, jwt-security]
- [ ] 3.5 Verificar que TODOS los endpoints tienen `response_model` explícito (no omitir en ningún caso) [skill: api-design]

## 4. Registro en main.py

- [ ] 4.1 Leer `backend/main.py` para entender cómo se registran los routers existentes (ej: `auth.router`) [skill: python-fastapi-ddd-skill]
- [ ] 4.2 Importar `perfil_router` e incluirlo bajo `prefix="/api/v1"` — igual que el patrón de `auth_router` [skill: python-fastapi-ddd-skill]

## 5. Tests — `backend/tests/test_perfil.py` (NUEVO)

- [ ] 5.1 Crear helper `_make_mock_usuario()` — igual que en `test_auth_login.py`, con campos `id, email, hashed_password, nombre, apellido, activo, telefono, creado_en` [skill: python-fastapi-ddd-skill]
- [ ] 5.2 Crear helper `_make_uow()` que retorne un `MagicMock` con `usuarios` como `AsyncMock` y `refresh_tokens` como `AsyncMock`; `uow.usuarios.update` y `uow.refresh_tokens.find_all_by` deben ser configurables [skill: python-fastapi-ddd-skill]
- [ ] 5.3 Clase `TestGetPerfilService`:
  - `test_get_perfil_returns_usuario_response` — `get_perfil(mock_user)` retorna instancia de `UsuarioResponse` con los mismos datos [skill: python-fastapi-ddd-skill]
- [ ] 5.4 Clase `TestUpdatePerfilService`:
  - `test_update_nombre_only` — solo `nombre` actualizado; `telefono` no se toca; `uow.usuarios.update` llamado una vez [skill: python-fastapi-ddd-skill]
  - `test_update_telefono_only` — solo `telefono` actualizado [skill: python-fastapi-ddd-skill]
  - `test_update_both_fields` — ambos campos actualizados correctamente [skill: python-fastapi-ddd-skill]
  - `test_update_returns_usuario_response` — el retorno es `UsuarioResponse` [skill: api-design]
- [ ] 5.5 Clase `TestCambiarPasswordService`:
  - `test_wrong_password_raises_400` — `verify_password` retorna `False` → `HTTPException(status_code=400)` [skill: jwt-security]
  - `test_correct_password_hashes_new_password` — `verify_password` retorna `True` → `hash_password` llamado con `nueva_password`; `current_user.hashed_password` actualizado [skill: jwt-security]
  - `test_correct_password_calls_uow_update` — `uow.usuarios.update` llamado con `current_user` [skill: python-fastapi-ddd-skill]
  - `test_revokes_all_active_refresh_tokens` — `uow.refresh_tokens.find_all_by` llamado con `usuario_id=current_user.id`; para cada token activo (`revoked_at is None`), `uow.refresh_tokens.update` llamado; tokens ya revocados NO se tocan [skill: jwt-security]
  - `test_already_revoked_tokens_not_updated` — tokens con `revoked_at` ya seteado no se vuelven a pasar a `update` [skill: jwt-security]
  - `test_returns_none_on_success` — la función retorna `None` (produce 204) [skill: api-design]
- [ ] 5.6 Clase `TestPerfilSchemas`:
  - `test_perfil_update_empty_raises_validation_error` — `PerfilUpdate()` sin campos lanza `ValidationError` [skill: api-design]
  - `test_cambiar_password_same_passwords_raises_validation_error` — `password_actual == nueva_password` lanza `ValidationError` [skill: api-design]
  - `test_cambiar_password_min_length` — `nueva_password` de 7 chars lanza `ValidationError` [skill: api-design]
  - `test_perfil_update_nombre_sanitized` — nombre con tags HTML es sanitizado (strip tags) [skill: python-fastapi-ddd-skill]

## 6. Verificación pre-archive

- [ ] 6.1 Correr `pytest backend/tests/test_perfil.py -v` — todos los tests deben pasar [skill: python-fastapi-ddd-skill]
- [ ] 6.2 Correr `pytest backend/ --cov=usuarios --cov-report=term-missing` — coverage de `usuarios/perfil_service.py` >= 80% [skill: python-fastapi-ddd-skill]
- [ ] 6.3 Correr `black --check backend/usuarios/perfil_router.py backend/usuarios/perfil_service.py backend/usuarios/perfil_schemas.py` [skill: python-fastapi-ddd-skill]
- [ ] 6.4 Correr `flake8 backend/usuarios/perfil_router.py backend/usuarios/perfil_service.py backend/usuarios/perfil_schemas.py` [skill: python-fastapi-ddd-skill]
- [ ] 6.5 Leer `.agents/skills/post-change-verification/SKILL.md` y ejecutar el health check post-change completo (uvicorn startup, Swagger accesible, endpoints responden 401 sin token) [skill: post-change-verification]
