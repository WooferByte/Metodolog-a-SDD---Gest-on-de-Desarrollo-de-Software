## ADDED Requirements

### Requirement: Logout endpoint revokes a refresh token
The system SHALL expose `POST /api/v1/auth/logout` that accepts a `RefreshRequest` body containing a `refresh_token` string and marks the matching `RefreshToken` row as revoked (`revoked_at = now()`).

#### Scenario: Successful logout with a valid active refresh token
- **WHEN** a client POSTs `{ "refresh_token": "<valid-active-token>" }` to `/api/v1/auth/logout`
- **THEN** the system SHALL set `revoked_at = now()` on the matching `RefreshToken` row and return HTTP 204 No Content with an empty body

#### Scenario: Logout is idempotent for already-revoked tokens
- **WHEN** a client POSTs a refresh token whose `revoked_at IS NOT NULL`
- **THEN** the system SHALL return HTTP 204 No Content (no error — session was already terminated)

#### Scenario: Logout rejects unknown refresh tokens
- **WHEN** a client POSTs a `refresh_token` string that has no matching row in the `refresh_tokens` table
- **THEN** the system SHALL return HTTP 401 Unauthorized

#### Scenario: Logout does not require an Authorization header
- **WHEN** a client POSTs to `/api/v1/auth/logout` without a `Authorization: Bearer` header
- **THEN** the system SHALL process the request normally using only the `refresh_token` body field as proof of session ownership

#### Scenario: Logout does not revoke other active sessions
- **WHEN** a user has two active refresh tokens (two concurrent sessions) and logs out with one of them
- **THEN** only the submitted token's `revoked_at` is set; the other token remains active
