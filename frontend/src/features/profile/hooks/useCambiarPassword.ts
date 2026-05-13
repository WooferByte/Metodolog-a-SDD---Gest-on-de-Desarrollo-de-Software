/**
 * useCambiarPassword — TanStack Query mutation for changing the user's password.
 *
 * POST /api/v1/perfil/cambiar-password
 * Returns 204 No Content — mutationFn returns void (no body parsing).
 *
 * onSuccess:
 *   1. Show success toast
 *   2. After 2000ms: call authStore.logout() → ProtectedRoute redirects to /login
 *
 * onError: NOT handled here — Axios interceptor handles 400 (wrong password)
 *   and 422 via RFC 7807 toast automatically.
 */

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'
import type { ChangePasswordPayload } from '@/features/profile/types/profile'

export function useCambiarPassword() {
  return useMutation<void, Error, ChangePasswordPayload>({
    mutationFn: async (payload: ChangePasswordPayload) => {
      // 204 No Content — do NOT attempt to parse response body
      await apiClient.post('/api/v1/perfil/cambiar-password', payload)
    },
    onSuccess: () => {
      useUIStore.getState().addToast({
        message: 'Contraseña actualizada. Iniciá sesión nuevamente.',
        type: 'success',
      })
      setTimeout(() => {
        useAuthStore.getState().logout()
        // ProtectedRoute detects isAuthenticated === false and redirects to /login
      }, 2000)
    },
    // onError: omitted — Axios interceptor handles 400/422 via RFC 7807 toast
  })
}
