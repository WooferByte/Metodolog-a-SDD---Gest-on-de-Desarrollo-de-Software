## ADDED Requirements

### Requirement: Admin can assign a role to a user
The system SHALL provide a `PUT /api/v1/admin/users/{user_id}/role` endpoint that allows an ADMIN to assign or change the role of any user in the system.

#### Scenario: Successful role assignment
- **WHEN** an authenticated ADMIN sends `PUT /api/v1/admin/users/{user_id}/role` with body `{"rol_nombre": "STOCK"}`
- **THEN** the system removes the user's current role and assigns the new role, returning HTTP 200 with the updated user data

#### Scenario: Non-admin cannot assign roles
- **WHEN** a user without ADMIN role sends `PUT /api/v1/admin/users/{user_id}/role`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Assigning the same role is idempotent
- **WHEN** an ADMIN assigns to a user the same role the user already holds
- **THEN** the system returns HTTP 200 without error

#### Scenario: Target user does not exist
- **WHEN** an ADMIN sends `PUT /api/v1/admin/users/{user_id}/role` with a non-existent `user_id`
- **THEN** the system returns HTTP 404 with RFC 7807 error body

#### Scenario: Invalid role name is rejected
- **WHEN** an ADMIN sends `PUT /api/v1/admin/users/{user_id}/role` with `{"rol_nombre": "SUPERUSER"}` (a role that does not exist in the system)
- **THEN** the system returns HTTP 422 Unprocessable Entity

### Requirement: Last admin protection
The system SHALL prevent the removal of the ADMIN role from the last active administrator in the system.

#### Scenario: Last admin cannot lose admin role
- **WHEN** an ADMIN who is the only ADMIN in the system attempts to change their own role to a non-ADMIN role
- **THEN** the system returns HTTP 409 Conflict with RFC 7807 error body indicating "Cannot remove the last admin"

#### Scenario: Admin can change role of other admin when multiple admins exist
- **WHEN** there are two or more users with the ADMIN role and an ADMIN changes another admin's role to a non-ADMIN role
- **THEN** the system performs the role change and returns HTTP 200

### Requirement: Get user roles
The system SHALL expose the current role(s) of a user through the role service for internal use by other services and for display in admin endpoints.

#### Scenario: Get roles of existing user
- **WHEN** `RoleService.get_user_roles(user_id)` is called with a valid user ID
- **THEN** the service returns the list of `UsuarioRol` records associated with that user

#### Scenario: Get roles of user with no roles
- **WHEN** `RoleService.get_user_roles(user_id)` is called for a user with no assigned roles
- **THEN** the service returns an empty list


### Requirement: Role assignment enforced at HTTP layer
The system SHALL enforce role-based access at the FastAPI router layer using `require_role`. The `rbac-role-assignment` capability is complete only when every protected endpoint declares its required roles via `Depends(require_role([...]))`.

#### Scenario: Role guard applied to write operations on catalog
- **WHEN** a request targets any non-GET endpoint under `/api/v1/productos`, `/api/v1/categorias`, or `/api/v1/ingredientes`
- **THEN** the endpoint SHALL have `require_role(["ADMIN", "STOCK"])` in its dependencies

#### Scenario: Role guard applied to order management
- **WHEN** a request targets `/api/v1/admin/pedidos` or `PATCH /api/v1/pedidos/{id}/avanzar`
- **THEN** the endpoint SHALL have `require_role(["ADMIN", "PEDIDOS"])` in its dependencies

#### Scenario: Role guard applied to user self-service
- **WHEN** a request targets `/api/v1/perfil` or `/api/v1/direcciones`
- **THEN** the endpoint SHALL have `require_role(["CLIENT"])` in its dependencies
