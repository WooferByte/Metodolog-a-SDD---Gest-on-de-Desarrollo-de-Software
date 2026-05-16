/**
 * useOrderDetail — TanStack Query v5 hook for fetching a single order with detail.
 *
 * Calls GET /api/v1/pedidos/{id}
 * Backend enforces ownership: CLIENT sees only their own orders; ADMIN sees all.
 *
 * Design decision D1 (design.md): Three independent hooks (useOrderDetail,
 * useCancelOrder, useAdvanceOrderState) for better tree-shaking and SRP.
 */

import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import type { OrderDetail } from '@/features/orders/types'

export const ORDER_DETAIL_QUERY_KEY = 'order-detail'

/**
 * Fetch the full detail of a single order.
 *
 * @param id - Order ID (must be a valid positive integer)
 * @returns TanStack Query result with OrderDetail data
 */
export function useOrderDetail(id: number) {
  return useQuery<OrderDetail>({
    queryKey: [ORDER_DETAIL_QUERY_KEY, id],
    queryFn: async () => {
      const response = await apiClient.get<OrderDetail>(`/api/v1/pedidos/${id}`)
      const data = response.data
      // Backend stores direccion_snapshot as a JSON string — parse to object
      if (data.direccion_snapshot && typeof data.direccion_snapshot === 'string') {
        try {
          data.direccion_snapshot = JSON.parse(data.direccion_snapshot as unknown as string)
        } catch {
          data.direccion_snapshot = null
        }
      }
      return data
    },
    enabled: id > 0,
    staleTime: 1000 * 60 * 2,    // 2 minutes
    gcTime: 1000 * 60 * 10,
    retry: 1,
  })
}
