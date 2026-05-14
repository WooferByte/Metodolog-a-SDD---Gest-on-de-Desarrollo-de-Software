/**
 * useCreateAddress — TanStack Query v5 mutation for creating a new address.
 *
 * POST /api/v1/direcciones
 * onSuccess: invalidates ['addresses'] cache + dispatches success toast
 * onError: NOT handled here — Axios interceptor dispatches RFC 7807 toast automatically
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useUIStore } from '@/store/uiStore'
import type { DireccionCreate, DireccionResponse } from '@/features/addresses/types'

export function useCreateAddress() {
  const qc = useQueryClient()

  return useMutation<DireccionResponse, Error, DireccionCreate>({
    mutationFn: (payload: DireccionCreate) =>
      apiClient.post<DireccionResponse>('/api/v1/direcciones', payload).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['addresses'] })
      useUIStore.getState().addToast({
        message: 'Dirección guardada.',
        type: 'success',
      })
    },
  })
}
