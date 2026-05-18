/**
 * usePaymentStatus — TanStack Query v5 query to check payment status post-redirect.
 *
 * GET /api/v1/pagos/{pedido_id}/status
 *
 * Only active when:
 *   - pedidoId is not null
 *   - paymentStore.status === 'waiting_payment'
 *
 * Used as a verification hook after MP redirects back to the app.
 * Polling can be enabled via refetchInterval if needed.
 *
 * Usage:
 *   const { data, isLoading } = usePaymentStatus()
 */

import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { usePaymentStore } from '@/store/paymentStore'
import type { PaymentStatusResponse } from '../types/payment.types'

async function fetchPaymentStatus(pedidoId: number): Promise<PaymentStatusResponse> {
  const { data } = await apiClient.get<PaymentStatusResponse>(
    `/api/v1/pagos/${pedidoId}/status`,
  )
  return data
}

/**
 * usePaymentStatus
 *
 * Returns TanStack Query v5 query for the current payment status.
 * Query is disabled unless pedidoId is set and status is 'waiting_payment'.
 */
export function usePaymentStatus() {
  const pedidoId = usePaymentStore((state) => state.pedidoId)
  const status = usePaymentStore((state) => state.status)

  const isActive = pedidoId !== null && status === 'waiting_payment'

  return useQuery<PaymentStatusResponse, Error>({
    queryKey: ['payment-status', pedidoId],
    queryFn: () => fetchPaymentStatus(pedidoId!),
    enabled: isActive,
    // Retry once — if status check fails, don't hammer the server
    retry: 1,
    // Stale after 10s — will refetch on window focus
    staleTime: 10_000,
  })
}
