/**
 * useDeleteAddress — TanStack Query v5 mutation for deleting an address.
 *
 * DELETE /api/v1/direcciones/{id}
 * Backend responds with 204 No Content on success.
 * onSuccess: invalidates ['addresses'] cache + dispatches success toast
 * onError: NOT handled here — Axios interceptor dispatches RFC 7807 toast automatically
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useUIStore } from '@/store/uiStore'

interface DeleteAddressVariables {
  id: number
}

export function useDeleteAddress() {
  const qc = useQueryClient()

  return useMutation<void, Error, DeleteAddressVariables>({
    mutationFn: ({ id }: DeleteAddressVariables) =>
      apiClient.delete(`/api/v1/direcciones/${id}`).then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['addresses'] })
      useUIStore.getState().addToast({
        message: 'Dirección eliminada.',
        type: 'success',
      })
    },
  })
}
