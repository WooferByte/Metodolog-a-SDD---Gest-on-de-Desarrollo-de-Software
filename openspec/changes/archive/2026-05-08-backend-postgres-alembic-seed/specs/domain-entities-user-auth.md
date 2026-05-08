# Specification: Domain Entities – User & Authentication

Core authentication and user management entities: Usuario, Rol, RefreshToken, DireccionEntrega.

## ADDED Requirements

### Requirement: Usuario Entity with Email Uniqueness and Password Hashing

The system SHALL store user credentials with email as unique business identifier and password stored as bcrypt hash.

#### Scenario: Create Usuario with valid email
- **WHEN** new Usuario created with email `user@foodstore.com` and password `securepass123`
- **THEN** email validated as RFC 5321 compliant
- **AND** password hashed with bcrypt (never stored plaintext)
- **AND** `creado_en` timestamp set to current UTC
- **AND** `actualizado_en` initialized to `creado_en`
- **AND** `eliminado_en` set to NULL (active)

#### Scenario: Enforce email uniqueness
- **WHEN** attempt to create second Usuario with same email
- **THEN** database constraint violation raised: `UNIQUE constraint failed: usuario.email`
- **AND** application catches error; returns HTTP 409 Conflict with message

#### Scenario: Usuario soft delete
- **WHEN** `usuario.eliminado_en` set to current timestamp
- **THEN** user cannot login (queries filter `WHERE eliminado_en IS NULL`)
- **AND** user data remains in database for compliance audit
- **AND** linked refresh tokens, addresses remain intact (FK referential integrity via CASCADE on DELETE not applied; soft delete only)

#### Scenario: Query active users
- **WHEN** repository queries users
- **THEN** default query: `SELECT * FROM usuario WHERE eliminado_en IS NULL`
- **AND** inactive (soft-deleted) users never appear unless explicitly requested

### Requirement: Rol Entity – Immutable Enum with Four Values

The system SHALL store role definitions (ADMIN, STOCK, PEDIDOS, CLIENT) as immutable reference data.

#### Scenario: Rol values are fixed
- **WHEN** application starts
- **THEN** exactly 4 roles exist: ADMIN, STOCK, PEDIDOS, CLIENT
- **AND** each role has `id`, `nombre` (unique), `descripcion`
- **AND** no UPDATE, DELETE allowed after initialization (application enforces)

#### Scenario: Assign role to usuario
- **WHEN** Usuario created with `rol_id` foreign key to Rol.id
- **THEN** constraint enforces role must exist
- **AND** user inherits permissions associated with role (enforced in API layer)

#### Scenario: Query by role
- **WHEN** application queries users with specific role (e.g., ADMIN users)
- **THEN** JOIN to rol table: `SELECT u.* FROM usuario u JOIN rol r ON u.rol_id = r.id WHERE r.nombre = 'ADMIN'`
- **AND** returns only active (non-soft-deleted) users

### Requirement: RefreshToken Entity with Revocation Tracking

The system SHALL issue short-lived JWT access tokens; longer-lived refresh tokens stored in database for revocation control.

#### Scenario: Issue refresh token on login
- **WHEN** user successfully authenticates
- **THEN** RefreshToken record created with fields:
  - `id` (primary key)
  - `usuario_id` (foreign key)
  - `token_hash` (bcrypt hash of JWT token, never stored plaintext)
  - `expires_at` (future timestamp, e.g., 30 days from now)
  - `revoked_at` (NULL initially; set when revoked)
  - `creado_en` (login timestamp)

#### Scenario: Refresh access token
- **WHEN** client sends refresh token in authorization header
- **THEN** application queries: `SELECT * FROM refresh_token WHERE token_hash = ? AND revoked_at IS NULL AND expires_at > NOW()`
- **AND** if found, issue new access token
- **AND** if revoked or expired, return HTTP 401 Unauthorized

#### Scenario: Revoke refresh token
- **WHEN** user logs out
- **THEN** `refresh_token.revoked_at` set to current UTC timestamp
- **AND** all future refresh attempts with this token fail
- **AND** historical record preserved for audit

#### Scenario: Clean up expired tokens
- **WHEN** background job runs (periodically)
- **THEN** delete RefreshToken records where `expires_at < NOW()` (cleanup; not required for correctness)
- **AND** revoked tokens kept for audit trail

### Requirement: DireccionEntrega Entity – Delivery Addresses with User Constraint

The system SHALL allow users to store multiple delivery addresses with validation and soft deletion support.

#### Scenario: Create delivery address for usuario
- **WHEN** Usuario creates new DireccionEntrega with:
  - `usuario_id` (foreign key)
  - `calle` (street address)
  - `numero` (street number)
  - `apartamento` (optional)
  - `ciudad` (city)
  - `codigo_postal` (postal code)
  - `pais` (country, default "AR")
  - `es_predeterminada` (boolean; default false)
- **THEN** all fields stored; no NULL except `apartamento`
- **AND** `creado_en`, `actualizado_en` set to current UTC
- **AND** `eliminado_en` set to NULL

#### Scenario: Mark address as default
- **WHEN** user sets `es_predeterminada = true` on one address
- **THEN** all other addresses for this user set `es_predeterminada = false` (single default)
- **AND** order creation uses default address unless explicitly overridden

#### Scenario: Soft delete address
- **WHEN** user deletes address
- **THEN** `eliminado_en` set to current timestamp
- **AND** address no longer appears in queries
- **AND** historical orders may still reference this address (not deleted; soft-deleted status independent)

#### Scenario: List user's active addresses
- **WHEN** application queries user's addresses
- **THEN** query filters: `SELECT * FROM direccion_entrega WHERE usuario_id = ? AND eliminado_en IS NULL`
- **AND** returns all active addresses, with default address first if applicable
