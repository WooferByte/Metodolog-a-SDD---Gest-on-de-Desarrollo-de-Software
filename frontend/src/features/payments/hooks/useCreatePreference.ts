/**
 * useCreatePreference — TanStack Query v5 mutation to create a MercadoPago preference.
 *
 * POST /api/v1/pagos/crear-preferencia
 * Body: { pedido_id: number }
 *
 * On success:
 *   - Stores preference_id, pago_id, init_point in paymentStore
 *   - Sets status to 'waiting_payment'
 *
 * Usage:
 *   const { mutate, isPending } = useCreatePreference()
 *   mutate({ pedido_id: 42 })
 */

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { usePaymentStore } from '@/store/paymentStore'
import type {
  CreatePreferenceRequest,
  CreatePreferenceResponse,
} from '../types/payment.types'

async function createPreference(
  payload: CreatePreferenceRequest,
): Promise<CreatePreferenceResponse> {
  const { data } = await apiClient.post<CreatePreferenceResponse>(
    '/api/v1/pagos/crear-preferencia',
    payload,
  )
  return data
}

/**
 * useCreatePreference
 *
 * Returns TanStack Query v5 mutation for creating an MP preference.
 * On success, updates paymentStore with preference data and sets status to waiting_payment.
 */
export function useCreatePreference() {
  const setPreference = usePaymentStore((state) => state.setPreference)
  const setStatus = usePaymentStore((state) => state.setStatus)
  const setError = usePaymentStore((state) => state.setError)

  return useMutation<CreatePreferenceResponse, Error, CreatePreferenceRequest>({
    mutationFn: createPreference,
    onSuccess: (data) => {
      setPreference(data.preference_id, data.pago_id, data.init_point)
      setStatus('idle') // preference ready — 'waiting_payment' is set by MercadoPagoButton on click
    },
    onError: (error) => {
      setError(error.message ?? 'Error al crear la preferencia de pago')
      // status is managed by the call-site (handlePay) — don't override here
    },
  })
}
