/**
 * PaymentStore - Checkout workflow and payment session state
 *
 * Features:
 * - Track selected payment method (mercadopago | cash | null)
 * - Track pedidoId, preferenceId, pagoId, initPoint from backend
 * - Payment status transitions: idle → creating_order → creating_preference → waiting_payment → success | error | pending
 * - ZERO persistence (no localStorage) — payment state is ephemeral by design
 * - Clears on every page reload (required for payment security)
 *
 * Usage:
 * ```typescript
 * const method = usePaymentStore((state) => state.method)
 * const status = usePaymentStore((state) => state.status)
 * const setMethod = usePaymentStore((state) => state.setMethod)
 * const reset = usePaymentStore((state) => state.reset)
 * ```
 *
 * Important Security Note:
 * Payment state must NEVER persist across page reloads to prevent payment hijacking.
 * If user refreshes mid-checkout, they must restart from step 1.
 */

import { create } from 'zustand'
import type { PaymentState } from '@/features/payments/types/payment.types'

/**
 * usePaymentStore — Zustand v5 store for the checkout payment flow.
 *
 * Uses create<T>()() double parentheses pattern (required for TypeScript middleware compat).
 * NO persist middleware — payment data is never stored in localStorage.
 */
export const usePaymentStore = create<PaymentState>()((set) => ({
  // Initial state
  method: null,
  pedidoId: null,
  preferenceId: null,
  pagoId: null,
  initPoint: null,
  status: 'idle',
  error: null,

  // Action: Set selected payment method
  // Also clears preference/pago state from any previous method selection
  setMethod: (method) =>
    set({
      method,
      preferenceId: null,
      pagoId: null,
      initPoint: null,
    }),

  // Action: Store the created pedido ID (set after successful POST /api/v1/pedidos)
  setPedidoId: (id) => set({ pedidoId: id }),

  // Action: Store preference data atomically (all 3 fields set together)
  setPreference: (preferenceId, pagoId, initPoint) =>
    set({ preferenceId, pagoId, initPoint }),

  // Action: Update payment flow status
  setStatus: (status) => set({ status }),

  // Action: Set error message (set null to clear)
  setError: (error) => set({ error }),

  // Action: Reset all state to initial values
  // Call after successful payment redirect, logout, or leaving checkout
  reset: () =>
    set({
      method: null,
      pedidoId: null,
      preferenceId: null,
      pagoId: null,
      initPoint: null,
      status: 'idle',
      error: null,
    }),
}))
