# auth-login Specification

## Purpose
TBD - created by archiving change auth-login. Update Purpose after archive.
## Requirements
### Requirement: Login endpoint accepts credentials and returns tokens
The system SHALL expose `POST /api/v1/auth/login` that accepts `LoginRequest` (email, password) and returns `TokenResponse` (access_token, refresh_token, token_type, usuario).

#### Scenario: Successful login with valid credentials
- **WHEN** a registered user POSTs valid email and password to `/api/v1/auth/login`
- **THEN** the system returns HTTP 200 with `access_token` (JWT, 30-min expiry), `refresh_token` (UUID string, 7-day expiry), `token_type="Bearer"`, and `usuario` object

#### Scenario: Login response contains correct token type
- **WHEN** a successful login response is received
- **THEN** `token_type` field equals `"Bearer"` (case-sensitive)

#### Scenario: Login response contains full user object
- **WHEN** a successful login response is received
- **THEN** `usuario` field contains a `UsuarioResponse` with at minimum: id, email, nombre, roles list

### Requirement: Access token payload contains user identity and roles
The system SHALL embed user identity and role names in the JWT access token payload.

#### Scenario: Access token sub claim is string user ID
- **WHEN** the JWT access token is decoded
- **THEN** the `sub` claim equals `str(user.id)` (string representation of the UUID user ID)

#### Scenario: Access token contains email
- **WHEN** the JWT access token is decoded
- **THEN** the `email` claim equals the user's email address

#### Scenario: Access token contains roles list
- **WHEN** the JWT access token is decoded
- **THEN** the `roles` claim is a list of role name strings (e.g., `["CLIENT"]`)

### Requirement: Refresh token is persisted to database
The system SHALL store each refresh token in the `RefreshToken` table upon successful login.

#### Scenario: RefreshToken row created on login
- **WHEN** a user successfully logs in
- **THEN** a new `RefreshToken` row is inserted with: `token = uuid4()`, `usuario_id = user.id`, `expires_at = now() + 7 days`, `revoked_at = NULL`

#### Scenario: Each login creates a distinct refresh token
- **WHEN** the same user logs in twice
- **THEN** two distinct `RefreshToken` rows exist, each with a unique `token` UUID

### Requirement: Login endpoint enforces rate limiting per IP
The system SHALL limit login attempts to a maximum of 5 requests per IP address per 15-minute window.

#### Scenario: Requests within limit succeed
- **WHEN** fewer than 5 login attempts are made from the same IP within 15 minutes
- **THEN** each attempt is processed normally (success or credential failure, not rate-limit rejection)

#### Scenario: Excess requests are rejected with 429
- **WHEN** 6 or more login attempts are made from the same IP within 15 minutes
- **THEN** the system returns HTTP 429 Too Many Requests for the 6th and subsequent attempts

### Requirement: Login returns generic error for invalid credentials
The system SHALL return HTTP 401 with the message `"Invalid credentials"` for any authentication failure, without revealing whether the email exists.

#### Scenario: Wrong password returns generic error
- **WHEN** a user POSTs a valid registered email with an incorrect password
- **THEN** the system returns HTTP 401 with `detail: "Invalid credentials"`

#### Scenario: Unknown email returns generic error
- **WHEN** a user POSTs an email that does not exist in the database
- **THEN** the system returns HTTP 401 with `detail: "Invalid credentials"` (same response as wrong password)

#### Scenario: Response time is consistent regardless of email existence
- **WHEN** two login attempts are made — one with a valid email (wrong password) and one with an unknown email
- **THEN** both responses take approximately the same time (bcrypt verification runs in both cases)



### Requirement: Login validates user active status
The system SHALL verify that `usuario.activo == True` during login. If the user account is inactive, the system SHALL return HTTP 403 before issuing any token.

#### Scenario: Active user logs in successfully
- **WHEN** a user with `activo=True` submits valid credentials
- **THEN** the system returns HTTP 200 with access and refresh tokens

#### Scenario: Inactive user is blocked at login
- **WHEN** a user with `activo=False` submits valid credentials
- **THEN** the system returns HTTP 403 with RFC 7807 body `{"type": "about:blank", "title": "Forbidden", "status": 403, "detail": "Cuenta desactivada"}`
- **AND** no token is issued
