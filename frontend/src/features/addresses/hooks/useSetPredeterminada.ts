/**
 * useSetPredeterminada — TanStack Query v5 mutation for marking an address as default.
 *
 * PATCH /api/v1/direcciones/{id}/predeterminada
 * No request body required.
 * onSuccess: invalidates ['addresses'] cache + dispatches success toast
 * onError: NOT handled here — Axios interceptor dispatches RFC 7807 toast automatically
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useUIStore } from '@/store/uiStore'
import type { DireccionResponse } from '@/features/addresses/types'

interface SetPredeterminadaVariables {
  id: number
}

export function useSetPredeterminada() {
  const qc = useQueryClient()

  return useMutation<DireccionResponse, Error, SetPredeterminadaVariables>({
    mutationFn: ({ id }: SetPredeterminadaVariables) =>
      apiClient
        .patch<DireccionResponse>(`/api/v1/direcciones/${id}/predeterminada`)
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['addresses'] })
      useUIStore.getState().addToast({
        message: 'Dirección predeterminada actualizada.',
        type: 'success',
      })
    },
  })
}
