## MODIFIED Requirements

### Requirement: Login validates user active status
The system SHALL verify that `usuario.activo == True` during login. If the user account is inactive, the system SHALL return HTTP 403 before issuing any token.

#### Scenario: Active user logs in successfully
- **WHEN** a user with `activo=True` submits valid credentials
- **THEN** the system returns HTTP 200 with access and refresh tokens

#### Scenario: Inactive user is blocked at login
- **WHEN** a user with `activo=False` submits valid credentials
- **THEN** the system returns HTTP 403 with RFC 7807 body `{"type": "about:blank", "title": "Forbidden", "status": 403, "detail": "Cuenta desactivada"}`
- **AND** no token is issued
