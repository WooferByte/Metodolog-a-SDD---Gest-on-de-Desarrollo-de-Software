/**
 * usePerfil — TanStack Query hook for fetching the authenticated user's profile.
 *
 * GET /api/v1/perfil
 * staleTime: 60s — avoids unnecessary refetches on window focus
 * placeholderData: keepPreviousData — prevents flicker when refocusing
 *
 * Error handling: delegated to the Axios interceptor (RFC 7807 toast).
 */

import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import type { PerfilData } from '@/features/profile/types/profile'

export function usePerfil() {
  return useQuery<PerfilData>({
    queryKey: ['perfil'],
    queryFn: () =>
      apiClient.get<PerfilData>('/api/v1/perfil').then((r) => r.data),
    staleTime: 60_000,
    placeholderData: keepPreviousData,
  })
}
