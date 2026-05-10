## Why

El sistema cuenta con 4 roles fijos (ADMIN, STOCK, PEDIDOS, CLIENT) definidos en BD y con RBAC aplicado a nivel de endpoints, pero no existe un endpoint administrativo para asignar o cambiar el rol de un usuario existente. Esto impide que un administrador gestione permisos sin acceso directo a la base de datos.

## What Changes

- Nuevo endpoint `PUT /api/v1/admin/users/{user_id}/role` para asignar o cambiar el rol de un usuario (solo ADMIN).
- Servicio `RoleService` con métodos: `get_user_roles()`, `assign_role()`, `remove_role()`.
- Validación de integridad: un ADMIN no puede quitarse a sí mismo el rol ADMIN si es el último admin activo del sistema.
- Los modelos `Rol`, `UsuarioRol` y `Usuario` ya existen; esta change solo agrega la capa de servicio y el endpoint.
- El rol CLIENT se asigna automáticamente en registro (ya implementado, no cambia).

## Capabilities

### New Capabilities
- `rbac-role-assignment`: Gestión administrativa de roles de usuario — asignar, cambiar y validar roles RBAC mediante API REST protegida por ADMIN.

### Modified Capabilities
- `security-jwt-hashing`: El sistema de autorización ahora debe validar también la condición de "último admin" al procesar cambios de rol, añadiendo una regla de negocio al contexto de seguridad RBAC.

## Impact

- **Backend**: Nuevo módulo o extensión en `backend/usuarios/` — `role_service.py`, `role_schemas.py`, extensión de `role_router.py`.
- **API**: Nuevo endpoint `PUT /api/v1/admin/users/{user_id}/role` protegido con `require_role(["ADMIN"])`.
- **BD**: Tabla `usuario_roles` (N:M con UNIQUE compuesta) — ya existe, solo se usa vía UoW.
- **Dependencias**: `auth-registration` (completado — `require_role` factory disponible en `backend/auth/dependencies.py`).
- **Tests**: Pruebas pytest para asignar rol, cambiar rol, validación último admin, y 403 para no-ADMIN.
