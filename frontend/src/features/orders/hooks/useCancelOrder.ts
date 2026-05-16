/**
 * useCancelOrder — TanStack Query v5 mutation for cancelling an order.
 *
 * Calls DELETE /api/v1/pedidos/{id}
 * Only available to CLIENT (own pending orders) or ADMIN.
 *
 * On success:
 *   - Closes the cancel modal via useOrderDetailStore
 *   - Shows a success toast via useUIStore
 *   - Invalidates ['orders'] and ['order-detail', id] queries
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useUIStore } from '@/store/uiStore'
import { useOrderDetailStore } from '@/features/orders/store/orderDetailStore'
import { ORDERS_QUERY_KEY } from '@/features/orders/hooks/useOrders'
import { ORDER_DETAIL_QUERY_KEY } from '@/features/orders/hooks/useOrderDetail'
import type { Order } from '@/features/orders/types'

export function useCancelOrder() {
  const queryClient = useQueryClient()
  const addToast = useUIStore((state) => state.addToast)
  const closeCancelModal = useOrderDetailStore((state) => state.closeCancelModal)

  return useMutation<Order, Error, number>({
    mutationFn: async (orderId: number) => {
      const response = await apiClient.delete<Order>(`/api/v1/pedidos/${orderId}`)
      return response.data
    },
    onSuccess: (_data, orderId) => {
      closeCancelModal()
      addToast({ message: 'Pedido cancelado correctamente', type: 'success' })
      // Invalidate the listing and detail caches so UI reflects the new state
      void queryClient.invalidateQueries({ queryKey: [ORDERS_QUERY_KEY] })
      void queryClient.invalidateQueries({ queryKey: [ORDER_DETAIL_QUERY_KEY, orderId] })
    },
  })
}
