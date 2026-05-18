/**
 * usePaymentStatusPolling
 *
 * Polls GET /api/v1/pagos/{pedidoId}/status every POLL_INTERVAL_MS (30s).
 * Stops automatically when the backend status moves out of 'pending'.
 * Updates paymentStore.status on terminal state transitions.
 * Retries on network errors (max 3, exponential backoff: 1s, 2s, 4s).
 *
 * Design decision: uses useEffect + setInterval (NOT refetchInterval from TanStack Query)
 * because polling with stop-by-content + custom retry is client state (Zustand territory),
 * not server state (TanStack Query territory). See design.md §5 for full rationale.
 *
 * @param pedidoId - Order ID to poll. Pass null to disable polling.
 * @returns        - { isPolling, retryCount, lastError }
 */

import { useEffect, useRef, useState } from 'react'
import { apiClient } from '@/shared/api/axios'
import { usePaymentStore } from '@/store/paymentStore'
import type { PaymentStatusResponse, PollingResult } from '../types/payment.types'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 30_000
const MAX_RETRIES = 3
const RETRY_DELAYS_MS = [1000, 2000, 4000]

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function usePaymentStatusPolling(pedidoId: number | null): PollingResult {
  // Granular selectors — one per field to avoid unnecessary re-renders
  const setStatus = usePaymentStore((state) => state.setStatus)
  const setError = usePaymentStore((state) => state.setError)
  const storeStatus = usePaymentStore((state) => state.status)

  const [isPolling, setIsPolling] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [lastError, setLastError] = useState<string | null>(null)

  // Ref for retryCount used inside setInterval callback — avoids stale closure
  // (the interval callback captures the ref on creation; ref.current is always fresh)
  const retryCountRef = useRef(0)

  const shouldPoll = pedidoId !== null && storeStatus === 'waiting_payment'

  useEffect(() => {
    if (!shouldPoll) {
      setIsPolling(false)
      return
    }

    // Reset polling state on activation
    setIsPolling(true)
    retryCountRef.current = 0
    setRetryCount(0)
    setLastError(null)

    // intervalId is declared with let so the poll() closure captures the reference
    // correctly even though setInterval runs after poll() is first called.
    let intervalId: ReturnType<typeof setInterval>

    // Async poll function with exponential retry on network errors
    const poll = async (): Promise<void> => {
      try {
        const { data } = await apiClient.get<PaymentStatusResponse>(
          `/api/v1/pagos/${pedidoId}/status`,
        )

        // Success — reset retry counter
        retryCountRef.current = 0
        setRetryCount(0)
        setLastError(null)

        if (data.estado === 'approved') {
          setStatus('success')
          clearInterval(intervalId)
          setIsPolling(false)
        } else if (data.estado === 'rejected' || data.estado === 'cancelled') {
          setStatus('error')
          clearInterval(intervalId)
          setIsPolling(false)
        } else if (data.estado === 'pending') {
          // Continue polling — no action needed
        } else {
          // Unknown status — stop and surface error
          setStatus('error')
          setError(`Estado de pago desconocido: ${data.estado}`)
          clearInterval(intervalId)
          setIsPolling(false)
        }
      } catch (err) {
        const current = retryCountRef.current

        if (current < MAX_RETRIES) {
          // Increment retry counter (both ref and state for UI visibility)
          retryCountRef.current = current + 1
          setRetryCount(current + 1)

          // Exponential backoff — wait before retrying
          const delay = RETRY_DELAYS_MS[current] ?? RETRY_DELAYS_MS[RETRY_DELAYS_MS.length - 1]
          await new Promise<void>((resolve) => setTimeout(resolve, delay))

          // Recursive retry — runs outside the interval to avoid accumulation
          poll()
        } else {
          // Retries exhausted — surface error and stop polling
          const msg = err instanceof Error ? err.message : 'Error al verificar el pago'
          setLastError(msg)
          setError(msg)
          clearInterval(intervalId)
          setIsPolling(false)
        }
      }
    }

    // First call is IMMEDIATE — user sees first verification without waiting 30s
    poll()

    // Subsequent polls every POLL_INTERVAL_MS
    intervalId = setInterval(poll, POLL_INTERVAL_MS)

    // Cleanup: guaranteed clearInterval when component unmounts or shouldPoll changes
    return () => {
      clearInterval(intervalId)
      setIsPolling(false)
    }
  }, [pedidoId, shouldPoll, setStatus, setError])

  return { isPolling, retryCount, lastError }
}
