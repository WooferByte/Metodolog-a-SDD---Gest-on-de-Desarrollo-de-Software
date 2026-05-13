/**
 * useUpdatePerfil — TanStack Query mutation for updating profile data.
 *
 * PUT /api/v1/perfil
 * onSuccess: invalidates ['perfil'] cache + dispatches success toast
 * onError: NOT handled here — Axios interceptor dispatches RFC 7807 toast automatically
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useUIStore } from '@/store/uiStore'
import type { PerfilData, UpdatePerfilPayload } from '@/features/profile/types/profile'

export function useUpdatePerfil() {
  const qc = useQueryClient()

  return useMutation<PerfilData, Error, UpdatePerfilPayload>({
    mutationFn: (payload: UpdatePerfilPayload) =>
      apiClient.put<PerfilData>('/api/v1/perfil', payload).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['perfil'] })
      useUIStore.getState().addToast({
        message: 'Perfil actualizado.',
        type: 'success',
      })
    },
    // onError: omitted — Axios interceptor handles 422 and other errors via RFC 7807 toast
  })
}
