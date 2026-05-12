## MODIFIED Requirements

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
