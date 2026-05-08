## Why

The frontend currently has a bare Axios instance (`shared/api/axios.ts`) with a placeholder comment noting that JWT auth interceptors will be added later. Without a centralized JWT interceptor, every API call must manually attach the Authorization header, and there is no automatic handling of token expiration — forcing users to log in again after every access token expiry even when a valid refresh token exists.

## What Changes

- Replace the placeholder Axios instance in `frontend/src/shared/api/axios.ts` with a fully configured instance that includes:
  - **Request interceptor**: Reads `accessToken` from `authStore` and injects `Authorization: Bearer <token>` header on every outgoing request.
  - **Response interceptor — refresh flow**: When a 401 response is received, automatically calls `POST /api/v1/auth/refresh` with the stored `refreshToken`, updates `authStore` with the new token pair via `updateTokens()`, and retries the original failed request.
  - **Queue mechanism**: Concurrent requests that arrive during an in-flight refresh are held in a queue; once the refresh resolves (or fails), all queued requests are either retried or rejected together — preventing multiple simultaneous refresh calls.
  - **Fallback on refresh failure**: If the refresh endpoint returns an error, call `authStore.logout()` and redirect the user to `/login`.

## Capabilities

### New Capabilities

- `axios-jwt-interceptor`: Centralized Axios HTTP client with automatic JWT attachment and transparent token refresh for all API calls from the React frontend.

### Modified Capabilities

- `zustand-auth-store`: The `updateTokens()` action is consumed by the interceptor to update both tokens after a successful refresh. The existing spec requirement "AuthStore handles token updates" already covers this; no spec-level behavior change is needed — the interceptor is a new consumer, not a new requirement.

## Impact

- **File changed**: `frontend/src/shared/api/axios.ts` — full rewrite with interceptors.
- **Reads from**: `frontend/src/store/authStore.ts` — accesses `accessToken`, `refreshToken`, `updateTokens()`, and `logout()`.
- **Backend dependency**: `POST /api/v1/auth/refresh` endpoint must accept `{ refresh_token: string }` and return `{ access_token, refresh_token }`.
- **Routing dependency**: App router must expose `/login` path; the interceptor redirects to this path on unrecoverable auth failures.
- **No new npm dependencies**: Axios is already installed; no additional packages required.
- **Existing consumers** of `apiClient` / `axiosInstance` exports receive the enhanced instance transparently — no call-site changes needed.
