/**
 * useUpdateAddress — TanStack Query v5 mutation for updating an existing address.
 *
 * PUT /api/v1/direcciones/{id}
 * onSuccess: invalidates ['addresses'] cache + dispatches success toast
 * onError: NOT handled here — Axios interceptor dispatches RFC 7807 toast automatically
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useUIStore } from '@/store/uiStore'
import type { DireccionUpdate, DireccionResponse } from '@/features/addresses/types'

interface UpdateAddressVariables {
  id: number
  data: DireccionUpdate
}

export function useUpdateAddress() {
  const qc = useQueryClient()

  return useMutation<DireccionResponse, Error, UpdateAddressVariables>({
    mutationFn: ({ id, data }: UpdateAddressVariables) =>
      apiClient.put<DireccionResponse>(`/api/v1/direcciones/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['addresses'] })
      useUIStore.getState().addToast({
        message: 'Dirección actualizada.',
        type: 'success',
      })
    },
  })
}
