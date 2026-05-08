## 1. Rewrite Axios Instance with Request Interceptor

- [ ] 1.1 Open `frontend/src/shared/api/axios.ts` and remove the placeholder response interceptor comment
- [ ] 1.2 Import `useAuthStore` from `../../store/authStore` (or `../../store`) at the top of the file
- [ ] 1.3 Add a request interceptor to `apiClient` that reads `useAuthStore.getState().accessToken` and sets `config.headers.Authorization = 'Bearer <token>'` when the token is non-null
- [ ] 1.4 Ensure requests where `accessToken` is null proceed without an Authorization header (no header mutation)

## 2. Implement Pending-Queue for Concurrent 401 Serialization

- [ ] 2.1 Declare module-level variables: `let isRefreshing = false` and `let pendingQueue: Array<{ resolve: (token: string) => void; reject: (error: unknown) => void }> = []`
- [ ] 2.2 Implement helper `drainQueue(token: string)` that calls `resolve(token)` for each entry in `pendingQueue` and resets the queue to `[]`
- [ ] 2.3 Implement helper `rejectQueue(error: unknown)` that calls `reject(error)` for each entry and resets the queue to `[]`

## 3. Implement Response Interceptor — Refresh Flow

- [ ] 3.1 Create a plain `refreshAxios` instance via `axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' })` with no interceptors attached — this is the instance used exclusively for the refresh call
- [ ] 3.2 Add a response interceptor to `apiClient` with an error handler that checks `error.response?.status === 401`
- [ ] 3.3 In the 401 branch: if `isRefreshing === true`, push a new deferred `{ resolve, reject }` onto `pendingQueue` and return the deferred promise (the promise resolves by retrying the original request with the new token once refresh completes)
- [ ] 3.4 If `isRefreshing === false`, set `isRefreshing = true` and call `refreshAxios.post('/api/v1/auth/refresh', { refresh_token: useAuthStore.getState().refreshToken })`
- [ ] 3.5 On refresh success: call `useAuthStore.getState().updateTokens(data.access_token, data.refresh_token)`, call `drainQueue(data.access_token)`, set `isRefreshing = false`, and retry the original request by returning `apiClient(originalConfig)` with the updated Authorization header
- [ ] 3.6 On refresh error: call `rejectQueue(refreshError)`, set `isRefreshing = false`, call `useAuthStore.getState().logout()`, set `window.location.href = '/login'`, and return `Promise.reject(refreshError)`
- [ ] 3.7 For non-401 errors, pass through immediately: `return Promise.reject(error)`

## 4. Preserve Public API

- [ ] 4.1 Verify `apiClient` is still exported as the default singleton instance (with interceptors wired)
- [ ] 4.2 Verify `axiosInstance` alias export still points to `apiClient`
- [ ] 4.3 Verify `createAxiosClient(baseURL)` factory export still exists and returns a plain configured instance (factory itself does NOT wire the auth interceptors — the singleton wiring is done once at module level)

## 5. TypeScript and Lint

- [ ] 5.1 Ensure no TypeScript errors (`tsc --noEmit`) in `shared/api/axios.ts` and any files it imports
- [ ] 5.2 Ensure no ESLint errors in the changed file (`npm run lint` from `frontend/`)
- [ ] 5.3 Annotate the `originalConfig` retry with proper type (`InternalAxiosRequestConfig`) to avoid `any` type warnings

## 6. Unit Tests

- [ ] 6.1 Create test file `frontend/src/shared/api/__tests__/axios.test.ts`
- [ ] 6.2 Write test: request interceptor attaches `Authorization: Bearer <token>` when `authStore.accessToken` is set
- [ ] 6.3 Write test: request interceptor does NOT attach Authorization header when `accessToken` is null
- [ ] 6.4 Write test: 401 response triggers one call to `POST /api/v1/auth/refresh`
- [ ] 6.5 Write test: after successful refresh, original request is retried and caller receives the response
- [ ] 6.6 Write test: concurrent 401s result in exactly one refresh call; all requests resolve after refresh
- [ ] 6.7 Write test: failed refresh calls `authStore.logout()` and sets `window.location.href = '/login'`
- [ ] 6.8 Write test: non-401 errors are rejected immediately without refresh attempt
- [ ] 6.9 Run `npm run test` from `frontend/` — all tests pass

## 7. Manual Smoke Test

- [ ] 7.1 Start backend (`uvicorn main:app --reload` from `backend/`) and frontend (`npm run dev` from `frontend/`)
- [ ] 7.2 Log in with a valid account — observe `Authorization` header in browser DevTools Network tab on any subsequent authenticated request
- [ ] 7.3 Simulate an expired access token by temporarily modifying `authStore.accessToken` in DevTools console to an invalid value, then make an authenticated request — observe the transparent refresh and retry
- [ ] 7.4 Simulate a fully expired session (clear localStorage + use an expired refresh token) — observe redirect to `/login` after refresh failure
