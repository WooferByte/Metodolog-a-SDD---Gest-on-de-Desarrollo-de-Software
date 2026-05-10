/**
 * Auth API functions — wraps HTTP calls to backend authentication endpoints.
 *
 * Pattern: Each function is a thin wrapper around the shared apiClient.
 * The caller (hook or store action) is responsible for error handling strategy.
 */

import { apiClient } from './axios'

/**
 * Call POST /api/v1/auth/logout to revoke the given refresh token server-side.
 *
 * Design decisions (from design.md):
 * - No Authorization header needed — refresh token IS the credential.
 * - Expects 204 No Content on success (including already-revoked tokens).
 * - On network error or non-204 HTTP error, this function lets the error
 *   propagate — the caller wraps it in try/catch for best-effort behaviour.
 *
 * @param refreshToken - The active refresh token to revoke.
 * @returns Promise<void> that resolves when the token has been revoked.
 * @throws AxiosError (or network error) if the backend returns a non-2xx status.
 */
export async function logoutUser(refreshToken: string): Promise<void> {
  await apiClient.post('/api/v1/auth/logout', { refresh_token: refreshToken })
}
