/**
 * useCreateOrder — TanStack Query v5 mutation to create a new order.
 *
 * POST /api/v1/pedidos
 *
 * On success:
 *   - Stores the returned pedido_id in paymentStore
 *   - Sets status to 'creating_preference'
 *
 * Body shape matches backend PedidoCreate schema:
 *   { direccion_entrega_id, forma_pago_id, observacion?, items[] }
 *
 * Usage:
 *   const { mutate, isPending, isError } = useCreateOrder()
 *   mutate({ direccion_entrega_id: 1, forma_pago_id: 1, items: [...] })
 */

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { usePaymentStore } from '@/store/paymentStore'
import type { CreateOrderResponse } from '../types/payment.types'

/** Line item for order creation — matches backend DetallePedidoCreate */
export interface CreateOrderItem {
  producto_id: number
  cantidad: number
  ingredientes_excluidos?: number[]
}

/** Request body for POST /api/v1/pedidos — matches backend PedidoCreate */
export interface CreateOrderRequest {
  direccion_entrega_id: number
  forma_pago_id: number
  observacion?: string
  items: CreateOrderItem[]
}

async function createOrder(payload: CreateOrderRequest): Promise<CreateOrderResponse> {
  const { data } = await apiClient.post<CreateOrderResponse>('/api/v1/pedidos', payload)
  return data
}

/**
 * useCreateOrder
 *
 * Returns TanStack Query v5 mutation for creating a pedido.
 * On success, updates paymentStore with the returned pedido ID.
 */
export function useCreateOrder() {
  const setPedidoId = usePaymentStore((state) => state.setPedidoId)
  const setStatus = usePaymentStore((state) => state.setStatus)
  const setError = usePaymentStore((state) => state.setError)

  return useMutation<CreateOrderResponse, Error, CreateOrderRequest>({
    mutationFn: createOrder,
    onSuccess: (data) => {
      setPedidoId(data.id)
      setStatus('creating_preference')
    },
    onError: (error) => {
      setError(error.message ?? 'Error al crear el pedido')
      // status is managed by the call-site (handlePay) — don't override here
    },
  })
}
