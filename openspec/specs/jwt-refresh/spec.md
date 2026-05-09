# jwt-refresh Specification

## Purpose
TBD - created by archiving change auth-token-refresh. Update Purpose after archive.
## Requirements
### Requirement: Refresh token endpoint issues new token pair

The system SHALL provide `POST /api/v1/auth/refresh` that accepts a `RefreshRequest` containing a `refresh_token` string and returns a `TokenResponse` with a new access token and a new refresh token.

#### Scenario: Valid refresh token returns new token pair
- **WHEN** the client sends a POST to `/api/v1/auth/refresh` with a `refresh_token` that exists in the DB, is not revoked (`revoked_at IS NULL`), and is not expired (`expires_at > now()`)
- **THEN** the system SHALL revoke the old token (set `revoked_at = now()`), create a new `RefreshToken` row, issue a new JWT access token and refresh token, and return HTTP 200 with `TokenResponse`

### Requirement: Refresh token rotation enforces one-time-use

The system SHALL revoke the presented refresh token immediately upon a successful refresh so that each token can only be used once.

#### Scenario: Reusing a consumed token is rejected
- **WHEN** the client presents a refresh token that was previously used (its `revoked_at` is set)
- **THEN** the system SHALL treat this as a replay attack, revoke ALL refresh tokens for that user, and return HTTP 401

### Requirement: Replay attack triggers full session revocation

The system SHALL detect replay attacks by checking `revoked_at` before accepting a token and, upon detection, SHALL revoke every active refresh token belonging to the same user.

#### Scenario: All tokens revoked on replay
- **WHEN** a refresh token with `revoked_at IS NOT NULL` is submitted
- **THEN** the system SHALL set `revoked_at = now()` on every `RefreshToken` row with the same `usuario_id` and return HTTP 401 with detail "Replay attack detected — all sessions revoked"

### Requirement: Expired refresh token is rejected

The system SHALL reject refresh tokens whose `expires_at` timestamp is in the past.

#### Scenario: Expired token returns 401
- **WHEN** the client sends a refresh token whose `expires_at < now(UTC)`
- **THEN** the system SHALL return HTTP 401 with detail "Refresh token expired"

### Requirement: Unknown refresh token is rejected

The system SHALL reject refresh tokens that do not exist in the `refresh_tokens` table.

#### Scenario: Counterfeit or deleted token returns 401
- **WHEN** the client sends a token string that has no matching row in `refresh_tokens`
- **THEN** the system SHALL return HTTP 401 with detail "Invalid refresh token"

