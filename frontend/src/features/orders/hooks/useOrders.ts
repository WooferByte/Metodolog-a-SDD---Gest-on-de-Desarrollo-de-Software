/**
 * useOrders — TanStack Query v5 hook for fetching paginated orders.
 *
 * - Uses keepPreviousData to avoid flash when changing pages (design.md D1).
 * - Calls GET /api/v1/pedidos with limit/offset and optional filter params.
 * - Backend filters by usuario_id from the JWT automatically for CLIENT role.
 * - Uses the shared apiClient which attaches Authorization header via interceptor.
 */

import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import type { OrdersPage, UseOrdersParams } from '@/features/orders/types'

export const ORDERS_QUERY_KEY = 'orders'

/**
 * Build URLSearchParams from UseOrdersParams, omitting undefined/null values.
 */
function buildOrdersQueryParams(params: UseOrdersParams): URLSearchParams {
  const p = new URLSearchParams()
  p.set('limit', String(params.limit ?? 10))
  p.set('offset', String(params.offset ?? 0))

  if (params.estadoId != null) {
    p.set('estado_pedido_id', String(params.estadoId))
  }
  if (params.search?.trim()) {
    p.set('q', params.search.trim())
  }
  if (params.fechaDesde?.trim()) {
    p.set('fecha_desde', params.fechaDesde.trim())
  }
  if (params.fechaHasta?.trim()) {
    p.set('fecha_hasta', params.fechaHasta.trim())
  }

  return p
}

/**
 * Fetches paginated orders from the backend.
 *
 * @param params - Pagination and filter params
 * @returns TanStack Query result with OrdersPage data
 */
export function useOrders(params: UseOrdersParams = {}) {
  const queryParams = buildOrdersQueryParams(params)

  return useQuery<OrdersPage>({
    queryKey: [ORDERS_QUERY_KEY, params],
    queryFn: async () => {
      const response = await apiClient.get<OrdersPage>(
        `/api/v1/pedidos?${queryParams.toString()}`,
      )
      return response.data
    },
    // Keep previous page data visible while new page is being fetched — avoids
    // content flash on pagination (vercel-react-best-practices: keepPreviousData)
    placeholderData: keepPreviousData,
    staleTime: 1000 * 60 * 2,   // 2 minutes — orders change more often than products
    gcTime: 1000 * 60 * 10,
    retry: 1,
  })
}
