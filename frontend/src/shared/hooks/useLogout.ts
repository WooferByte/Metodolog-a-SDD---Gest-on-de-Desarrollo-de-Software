/**
 * useLogout — async logout hook that revokes the refresh token server-side
 * before clearing local auth state.
 *
 * Best-effort pattern (from design.md Decision 4):
 * 1. POST to /api/v1/auth/logout with the current refreshToken.
 * 2. Always clear authStore state in the `finally` block regardless of the
 *    HTTP outcome — the user's local session is ALWAYS terminated.
 *
 * This means:
 * - If the backend call succeeds → token is revoked server-side AND locally.
 * - If the backend call fails (network error, 5xx) → token still expires
 *   naturally (7-day TTL), but local state is cleared immediately.
 *
 * Usage:
 * ```tsx
 * const { logout, isLoading } = useLogout()
 * <button onClick={logout} disabled={isLoading}>Logout</button>
 * ```
 */

import { useState, useCallback } from 'react'
import { useAuthStore } from '../../store/authStore'
import { logoutUser } from '../api/authApi'

export interface UseLogoutReturn {
  /** Triggers async logout — calls backend then clears local state */
  logout: () => Promise<void>
  /** True while the backend call is in flight (use to disable UI) */
  isLoading: boolean
}

/**
 * Hook that provides an async logout action.
 *
 * The hook is loading-state-aware so components can show a disabled/spinner
 * state during the async call to prevent double-submission.
 */
export function useLogout(): UseLogoutReturn {
  const [isLoading, setIsLoading] = useState(false)
  const clearAuthState = useAuthStore((state) => state.logout)
  const refreshToken = useAuthStore((state) => state.refreshToken)

  const logout = useCallback(async () => {
    if (isLoading) return // prevent double-submission
    setIsLoading(true)
    try {
      // Best-effort: attempt server-side revocation
      if (refreshToken) {
        await logoutUser(refreshToken)
      }
    } catch {
      // Network error or backend error — still clear local state below
      // The refresh token will expire naturally (7-day TTL)
    } finally {
      // Always clear local state regardless of backend response
      clearAuthState()
      setIsLoading(false)
    }
  }, [refreshToken, clearAuthState, isLoading])

  return { logout, isLoading }
}
