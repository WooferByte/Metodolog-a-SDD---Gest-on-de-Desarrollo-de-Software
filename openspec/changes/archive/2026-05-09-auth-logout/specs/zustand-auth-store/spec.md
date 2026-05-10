## MODIFIED Requirements

### Requirement: AuthStore has logout action
The authStore SHALL provide a `logout()` mechanism that calls the backend `POST /api/v1/auth/logout` endpoint with the current refresh token to revoke it server-side, and THEN clears all authentication state (tokens, user) from the store and localStorage, regardless of whether the backend call succeeds.

#### Scenario: Successful backend revocation then local state clear
- **WHEN** an authenticated user triggers logout and the backend responds with HTTP 204
- **THEN** the system SHALL clear `accessToken`, `refreshToken`, and `user` from authStore; `isAuthenticated` becomes false; `accessToken` is removed from localStorage

#### Scenario: Logout clears local state even when backend call fails
- **WHEN** an authenticated user triggers logout and the network request to `/api/v1/auth/logout` fails (timeout, 5xx, network error)
- **THEN** the system SHALL still clear all auth state from authStore and localStorage (best-effort revocation)

#### Scenario: Remove persisted token
- **WHEN** user logs out
- **THEN** `accessToken` is removed from localStorage (the `food-store-auth` key no longer contains an `accessToken`)
