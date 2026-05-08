## Context

The Food Store frontend uses Axios for all HTTP calls to the FastAPI backend. The current `shared/api/axios.ts` exports a singleton `apiClient` with a no-op response interceptor, explicitly leaving JWT handling for a future change. The `authStore` (Zustand) already manages `accessToken`, `refreshToken`, `updateTokens()`, and `logout()`. Backend access tokens expire after 30 minutes; refresh tokens last 7 days.

The interceptor must work transparently: every module that imports `apiClient` or `axiosInstance` must automatically get token injection and refresh without modification.

## Goals / Non-Goals

**Goals:**
- Inject `Authorization: Bearer <token>` on every request when an access token is present.
- Detect 401 responses and transparently attempt one token refresh cycle.
- Serialize concurrent 401 failures behind a single refresh call to avoid thundering-herd on the refresh endpoint.
- On unrecoverable auth failure (refresh error), clear auth state and redirect to `/login`.
- Keep the public API of `shared/api/axios.ts` unchanged (`apiClient`, `axiosInstance`, `createAxiosClient`).

**Non-Goals:**
- Implementing the backend `/auth/refresh` endpoint (already exists or is covered by a separate change).
- Refresh token rotation detection / replay attack protection (backend responsibility).
- Offline/network-retry logic beyond the single refresh attempt.
- Handling other 4xx/5xx errors beyond the 401 refresh flow.

## Decisions

### Decision 1: Read tokens directly from Zustand store getState() (not hooks)

**Chosen**: Call `useAuthStore.getState()` inside interceptors. Axios interceptors run outside of React's render cycle, so React hooks cannot be used. Zustand's `getState()` is the correct escape hatch for non-component contexts.

**Alternative considered**: Pass tokens as closure variables captured at instance creation time. Rejected because tokens change on refresh; a stale closure would always send the old token.

### Decision 2: Pending-queue pattern for concurrent 401s

**Chosen**: Maintain a module-level `isRefreshing` boolean and a `pendingQueue: Array<{resolve, reject}>`. When a 401 arrives:
1. If `isRefreshing === false`, start the refresh and set `isRefreshing = true`.
2. If `isRefreshing === true`, push a deferred `{resolve, reject}` onto `pendingQueue` and return the deferred promise.
3. On refresh success, drain the queue by calling each `resolve(token)` and let each queued request retry with the new token.
4. On refresh failure, drain the queue by calling each `reject(error)`, then logout and redirect.

**Alternative considered**: Let each 401 independently call refresh. Rejected — multiple simultaneous refresh calls with the same refresh token trigger replay detection on the backend (or at minimum waste requests and race on token update).

### Decision 3: Retry original request using a separate internal Axios instance for the refresh call

**Chosen**: Issue the refresh `POST` directly with `axios.create()` (a plain instance with no interceptors), not through `apiClient`. This prevents the refresh call from itself triggering the interceptor and entering an infinite loop.

**Alternative considered**: Add a custom header flag (e.g., `_retry: true`) to the config of the retry request and skip the interceptor if that flag is set. Viable but brittle — easier to just use a plain axios instance for the refresh call.

### Decision 4: Redirect via window.location.href, not React Router

**Chosen**: `window.location.href = '/login'` on unrecoverable auth failure. The interceptor lives in `shared/api/` outside React's component tree; importing the router instance from the app layer would create an upward FSD import violation (shared → app).

**Alternative considered**: Emit a custom DOM event that the App component listens to and triggers navigation. More correct architecturally but adds complexity for minimal gain in a non-SSR project.

### Decision 5: Keep createAxiosClient factory for testing

The existing `createAxiosClient(baseURL)` factory is preserved. This lets tests create isolated instances without interceptors by calling the factory without wiring up the store interceptors, or by mocking the store.

## Risks / Trade-offs

- **Race condition on queue drain**: If `updateTokens()` is async in the future, there is a short window where drained requests might use a stale token. Current `updateTokens()` is synchronous Zustand state — low risk.

  → Mitigation: Pass the new token explicitly to each queued request's config header rather than re-reading from store, ensuring consistency across the entire drain cycle.

- **Redirect loop**: If the backend returns 401 for the refresh endpoint itself (e.g., refresh token also expired), the interceptor will call logout + redirect. If `/login` page itself makes an authenticated API call, it could trigger another 401. 

  → Mitigation: The request interceptor only adds the Bearer header when `accessToken !== null`. After logout, the store clears tokens, so `/login` requests go without auth headers — no loop.

- **window.location.href causes a full page reload**: Any in-memory state (cart not yet persisted, etc.) will be lost.

  → Mitigation: `cartStore` is persisted to localStorage; payment and UI state are intentionally ephemeral. Acceptable trade-off.

- **Zustand store not hydrated yet on first request**: On cold load, `_hasHydrated` may be false. The interceptor reads `accessToken` which will be `null` until hydration completes.

  → Mitigation: TanStack Query's `enabled` flags and protected route guards in the app layer should prevent authenticated requests before the store hydrates. The interceptor itself needs no change.

## Migration Plan

1. Rewrite `frontend/src/shared/api/axios.ts` in place — exports remain identical.
2. No changes required to any existing consumer of `apiClient` or `axiosInstance`.
3. Verify the backend `/api/v1/auth/refresh` endpoint contract: `POST` with body `{ refresh_token: string }`, response `{ access_token: string, refresh_token: string }`.
4. Manual smoke test: Log in, wait for (or simulate) token expiry, make an authenticated request, observe transparent refresh and retry.

**Rollback**: Revert `axios.ts` to the previous version. No database migrations, no other files changed.

## Open Questions

- Confirm the exact JSON field names returned by `POST /api/v1/auth/refresh` (`access_token` + `refresh_token`? or `accessToken` + `refreshToken`?). FastAPI convention suggests snake_case — using `access_token` / `refresh_token` in this design.
- Should the interceptor also handle 403 (forbidden) responses to trigger logout? Out of scope for this change but worth noting for a follow-up.
