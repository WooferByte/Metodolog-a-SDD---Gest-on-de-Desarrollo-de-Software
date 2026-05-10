## Context

El sistema Food Store implementa RBAC con 4 roles fijos: ADMIN, STOCK, PEDIDOS, CLIENT. Los modelos `Rol`, `UsuarioRol` y `Usuario` ya existen en `backend/core/models.py`. La tabla `usuario_roles` tiene una restricción UNIQUE compuesta `(usuario_id, rol_id)`. El UoW en `backend/infrastructure/uow.py` ya expone `uow.roles` y `uow.usuario_roles`. El factory `require_role()` está en `backend/auth/dependencies.py`.

La funcionalidad de registro asigna el rol CLIENT automáticamente. Sin embargo, no existe un endpoint administrativo para cambiar o asignar roles a usuarios existentes, lo que obliga a intervención directa en BD.

## Goals / Non-Goals

**Goals:**
- Endpoint `PUT /api/v1/admin/users/{user_id}/role` protegido con `require_role(["ADMIN"])`.
- Servicio `RoleService` con operaciones: `get_user_roles()`, `assign_role()`, `remove_role()`.
- Validación: el último ADMIN activo no puede perder el rol ADMIN.
- Tests pytest para todos los casos de uso y restricciones.

**Non-Goals:**
- Gestión de roles dinámicos o creación de nuevos roles (los 4 roles son fijos en BD).
- UI/frontend para la administración de roles.
- Historial de auditoría de cambios de rol (posible change futura).
- Asignación de múltiples roles simultáneamente (un usuario puede tener un solo rol activo principal; la tabla permite N:M pero el endpoint gestiona rol por rol).

## Decisions

### D1: Módulo en `backend/usuarios/` (no en `backend/auth/`)

**Decisión**: El servicio y router de roles se implementan dentro del módulo `usuarios/` como `role_service.py` y extensión del router de usuarios, no en `auth/`.

**Rationale**: La gestión de roles es una operación de administración de usuarios, no de autenticación. `auth/` contiene lógica de login/tokens; `usuarios/` contiene la entidad Usuario con sus atributos. Separar concerns evita que `auth/` crezca con lógica de negocio de usuario.

**Alternativa descartada**: Crear un módulo independiente `backend/roles/`. Innecesario dado el scope reducido — un servicio y un endpoint no justifican un módulo propio.

### D2: Endpoint `PUT /api/v1/admin/users/{user_id}/role` (reemplaza el rol)

**Decisión**: Un único método PUT que reemplaza el rol actual del usuario. El body contiene `{ "rol_nombre": "STOCK" }`. La operación es idempotente: asignar el mismo rol que ya tiene el usuario no falla.

**Rationale**: El modelo de negocio trata el rol como un atributo singular del usuario (aunque la tabla es N:M, en la práctica cada usuario tiene un rol activo). PUT semántico para reemplazo es correcto según REST. Simplifica el contrato de API.

**Alternativa descartada**: `POST /assign` y `DELETE /remove` separados. Más verboso, más endpoints, más tests, sin ganancia funcional real dado el modelo de un-rol-por-usuario.

### D3: Validación "último admin" en la capa de servicio

**Decisión**: `RoleService.assign_role()` verifica, antes de cambiar el rol, si el usuario es ADMIN y si quedaría al menos un ADMIN activo tras el cambio. Si el usuario que cambia el rol es el único ADMIN, la operación falla con HTTP 409.

**Rationale**: La validación pertenece a la lógica de negocio (servicio), no al router. El router solo traduce HTTP ↔ dominio. Usar HTTP 409 Conflict con RFC 7807 body es semánticamente correcto: el estado actual del recurso entra en conflicto con la operación solicitada.

**Alternativa descartada**: Validar en el router. Viola separación de concerns — el router no debería conocer reglas de negocio.

### D4: Usar `selectinload()` para cargar relaciones

**Decisión**: Al cargar `UsuarioRol` del usuario, usar `selectinload()` explícito en la query async. No depender de lazy loading.

**Rationale**: FastAPI + SQLModel con AsyncSession no soporta lazy loading implícito. Bug conocido del proyecto: acceder a relaciones sin `selectinload()` causa `MissingGreenlet` error en runtime.

### D5: `datetime.utcnow()` para timestamps

**Decisión**: Usar `datetime.utcnow()` en todos los campos de fecha (`creado_en`, `actualizado_en` en `UsuarioRol`).

**Rationale**: Bug conocido del proyecto: `datetime.now(UTC)` produce valores con timezone-aware que generan incompatibilidades con las columnas `TIMESTAMP WITHOUT TIME ZONE` de PostgreSQL.

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|-----------|
| Race condition: dos requests simultáneos intentan quitar el último admin | Usar `SELECT FOR UPDATE` al contar admins activos dentro de la misma transacción UoW |
| El endpoint permite a un ADMIN degradarse a sí mismo mientras hay otros ADMINs | Comportamiento correcto y esperado; solo se bloquea si es el último ADMIN |
| N:M tabla `usuario_roles` permite múltiples roles, pero el endpoint asume uno | El servicio hace `remove_role()` del rol actual antes de `assign_role()` del nuevo, manteniendo exactamente un rol activo |

## Migration Plan

1. No hay cambios de esquema de BD (tablas y roles ya existen).
2. Deploy: agregar los nuevos archivos `role_service.py`, `role_schemas.py` y el nuevo router.
3. Registrar el nuevo router en `main.py`.
4. No hay rollback complejo — eliminar los archivos nuevos y el registro en `main.py` revierte el cambio.

## Open Questions

- ¿Un usuario puede tener cero roles? (Actualmente el seed garantiza que todo usuario tiene al menos CLIENT, pero el endpoint podría dejar un usuario sin rol si se llama `remove_role` directamente.) → Decisión: el endpoint PUT siempre asigna un rol nuevo, no permite dejar usuario sin rol.
