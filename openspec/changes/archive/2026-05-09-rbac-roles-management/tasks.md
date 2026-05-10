## 1. Verificación de modelos existentes

- [x] 1.1 Leer `backend/core/models.py` y verificar que `Rol`, `UsuarioRol` y `Usuario` tienen los campos necesarios (`id`, `nombre`, `usuario_id`, `rol_id`, `creado_en`)
- [x] 1.2 Leer `backend/infrastructure/uow.py` y confirmar que `uow.roles` y `uow.usuario_roles` están disponibles como repositorios
- [x] 1.3 Leer `backend/auth/dependencies.py` y confirmar la firma del factory `require_role()`

## 2. Schemas de request/response

- [x] 2.1 Crear `backend/usuarios/role_schemas.py` con `AssignRoleRequest(BaseModel)` — campo `rol_nombre: str` con validación de valores permitidos (ADMIN, STOCK, PEDIDOS, CLIENT)
- [x] 2.2 Agregar `AssignRoleResponse(BaseModel)` con `user_id`, `rol_nombre` y `mensaje` para confirmar la operación

## 3. Servicio de roles

- [x] 3.1 Crear `backend/usuarios/role_service.py` con clase `RoleService`
- [x] 3.2 Implementar `get_user_roles(uow, user_id) -> list[UsuarioRol]` — usar `selectinload()` para evitar lazy loading en AsyncSession
- [x] 3.3 Implementar `assign_role(uow, user_id, rol_nombre) -> AssignRoleResponse` con lógica:
  - Verificar que el usuario existe (HTTP 404 si no)
  - Verificar que el rol existe en BD (HTTP 422 si no)
  - Verificar protección "último admin": si el usuario tiene rol ADMIN y `rol_nombre != "ADMIN"`, contar admins activos; si queda solo 1, lanzar HTTP 409
  - Usar `SELECT FOR UPDATE` al contar admins para evitar race condition
  - Remover rol actual con `remove_role()` y asignar el nuevo
  - Usar `datetime.utcnow()` (NO `datetime.now(UTC)`) para timestamps
- [x] 3.4 Implementar `remove_role(uow, user_id, rol_nombre) -> None` — eliminar el registro `UsuarioRol` correspondiente; no falla si no existe (idempotente)

## 4. Router / Endpoint

- [x] 4.1 Crear `backend/usuarios/role_router.py` con `APIRouter(prefix="/api/v1/admin/users", tags=["admin-roles"])`
- [x] 4.2 Implementar `PUT /{user_id}/role` con:
  - Dependencia `current_user: Usuario = Depends(require_role(["ADMIN"]))`
  - Body `AssignRoleRequest`
  - Retorno `AssignRoleResponse` con HTTP 200
  - Manejo de excepciones: HTTP 404, 409, 422 con body RFC 7807
- [x] 4.3 Registrar el router en `backend/main.py` con `app.include_router(role_router)`

## 5. Tests automáticos (pytest)

- [x] 5.1 Crear `backend/tests/test_rbac_roles.py` con fixtures de BD en memoria (o mocks de UoW)
- [x] 5.2 Test: `test_assign_role_success` — ADMIN asigna rol STOCK a usuario CLIENT → HTTP 200, rol cambiado
- [x] 5.3 Test: `test_assign_same_role_idempotent` — ADMIN asigna el mismo rol que ya tiene el usuario → HTTP 200 sin error
- [x] 5.4 Test: `test_assign_role_user_not_found` — `user_id` inexistente → HTTP 404
- [x] 5.5 Test: `test_assign_invalid_role_name` — rol "SUPERUSER" → HTTP 422
- [x] 5.6 Test: `test_last_admin_protection` — único ADMIN intenta cambiar su propio rol a STOCK → HTTP 409
- [x] 5.7 Test: `test_multiple_admins_can_change_role` — hay 2 ADMINs, uno cambia el rol del otro → HTTP 200
- [x] 5.8 Test: `test_non_admin_forbidden` — usuario STOCK llama al endpoint → HTTP 403
- [x] 5.9 Ejecutar `pytest backend/tests/test_rbac_roles.py -v` y confirmar que todos los tests pasan (21/21 passed)
- [ ] 5.10 Ejecutar `poetry run ruff check backend/usuarios/` y `poetry run black --check backend/usuarios/` para lint

## 6. Validación manual (guía de testing)

- [ ] 6.1 Levantar el entorno: `docker-compose up -d` + `uvicorn main:app --reload` desde `backend/`
- [ ] 6.2 Autenticarse como ADMIN en `POST /api/v1/auth/login` y copiar el `access_token`
- [ ] 6.3 Listar usuarios con `GET /api/v1/admin/users` para obtener un `user_id` de usuario CLIENT
- [ ] 6.4 Ejecutar `PUT /api/v1/admin/users/{user_id}/role` con body `{"rol_nombre": "STOCK"}` y verificar HTTP 200
- [ ] 6.5 Verificar en BD: `docker exec -it foodstore-postgres psql -U postgres -d foodstore_db -c "SELECT u.email, r.nombre FROM usuarios u JOIN usuario_roles ur ON u.id=ur.usuario_id JOIN roles r ON r.id=ur.rol_id WHERE u.id={user_id};"`
- [ ] 6.6 Intentar cambiar el rol del único ADMIN a STOCK → verificar HTTP 409 con mensaje "Cannot remove the last admin"
- [ ] 6.7 Intentar llamar al endpoint con token de usuario STOCK → verificar HTTP 403

## 7. Confirmación de completitud

- [ ] 7.1 Todos los tests automáticos pasan (`pytest` sin errores)
- [ ] 7.2 Todos los pasos de validación manual completados y verificados
- [ ] 7.3 No hay archivos `.env` ni secretos incluidos en los cambios (`git status` limpio excepto archivos de código)
- [ ] 7.4 Change lista para archivar — informar al usuario para ejecutar `openspec archive change "rbac-roles-management"`
