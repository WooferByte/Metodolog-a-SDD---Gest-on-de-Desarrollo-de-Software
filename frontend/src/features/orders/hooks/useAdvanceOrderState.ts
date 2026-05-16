/**
 * useAdvanceOrderState — TanStack Query v5 mutation for advancing order FSM state.
 *
 * Calls PATCH /api/v1/pedidos/{id}/estado
 * Body: { nuevo_estado_id: number } — field name verified in backend/pedidos/schemas.py
 * Only available to ADMIN and PEDIDOS roles.
 *
 * On success:
 *   - Shows a success toast via useUIStore
 *   - Invalidates ['orders'] and ['order-detail', id] queries
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useUIStore } from '@/store/uiStore'
import { ORDERS_QUERY_KEY } from '@/features/orders/hooks/useOrders'
import { ORDER_DETAIL_QUERY_KEY } from '@/features/orders/hooks/useOrderDetail'
import type { Order } from '@/features/orders/types'

export interface AdvanceOrderStateParams {
  orderId: number
  nuevoEstadoId: number
}

export function useAdvanceOrderState() {
  const queryClient = useQueryClient()
  const addToast = useUIStore((state) => state.addToast)

  return useMutation<Order, Error, AdvanceOrderStateParams>({
    mutationFn: async ({ orderId, nuevoEstadoId }: AdvanceOrderStateParams) => {
      const response = await apiClient.patch<Order>(
        `/api/v1/pedidos/${orderId}/estado`,
        { nuevo_estado_id: nuevoEstadoId },
      )
      return response.data
    },
    onSuccess: (_data, { orderId }) => {
      addToast({ message: 'Estado del pedido actualizado', type: 'success' })
      void queryClient.invalidateQueries({ queryKey: [ORDERS_QUERY_KEY] })
      void queryClient.invalidateQueries({ queryKey: [ORDER_DETAIL_QUERY_KEY, orderId] })
    },
  })
}
