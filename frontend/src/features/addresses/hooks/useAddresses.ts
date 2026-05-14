/**
 * useAddresses — TanStack Query v5 hook for fetching the authenticated user's addresses.
 *
 * GET /api/v1/direcciones
 * queryKey: ['addresses']
 * staleTime: 30s — avoids unnecessary refetches on window focus
 *
 * Error handling: delegated to the Axios interceptor (RFC 7807 toast).
 */

import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import type { DireccionResponse } from '@/features/addresses/types'

export function useAddresses() {
  return useQuery<DireccionResponse[]>({
    queryKey: ['addresses'],
    queryFn: () =>
      apiClient.get<DireccionResponse[]>('/api/v1/direcciones').then((r) => r.data),
    staleTime: 30_000,
  })
}
