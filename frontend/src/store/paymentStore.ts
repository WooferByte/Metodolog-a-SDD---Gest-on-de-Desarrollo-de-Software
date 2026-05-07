/**
 * PaymentStore - Checkout workflow and payment state
 * 
 * Features:
 * - Multi-step checkout process (cart → shipping → payment → confirmation)
 * - Payment status tracking (idle, processing, completed, failed)
 * - Preference ID management for payment providers (MercadoPago)
 * - ZERO persistence for security (explicit empty storage config)
 * - Clears on every page reload (required for payment security)
 * 
 * Important Security Note:
 * Payment state must NEVER persist across page reloads to prevent payment hijacking.
 * If user refreshes mid-checkout, they must restart from step 1.
 * This is an acceptable UX trade-off for security.
 * 
 * Usage:
 * ```typescript
 * const { checkoutStep, paymentStatus } = usePaymentStore()
 * const startCheckout = usePaymentStore((state) => state.startCheckout)
 * const resetPayment = usePaymentStore((state) => state.resetPayment)
 * ```
 */

import { create } from 'zustand'
import type { PaymentStore } from './types'

/**
 * Create paymentStore with TypeScript support and NO persistence
 * 
 * Important: Uses create<T>()() double parentheses pattern (future-proof)
 * NO persist middleware - payment data is never stored in localStorage
 */
export const usePaymentStore = create<PaymentStore>()((set) => ({
  // Initial state
  checkoutStep: 'cart',
  preferenceId: null,
  paymentStatus: 'idle',

  // Action: Initialize checkout workflow
  startCheckout: () =>
    set({
      checkoutStep: 'shipping',
      paymentStatus: 'idle',
      preferenceId: null,
    }),

  // Action: Set MercadoPago preference ID after creating preference
  setPreference: (preferenceId: string) =>
    set({
      preferenceId,
      checkoutStep: 'payment',
    }),

  // Action: Update payment status as checkout progresses
  updatePaymentStatus: (status: PaymentStore['paymentStatus']) =>
    set({ paymentStatus: status }),

  // Action: Reset payment state to initial state
  // Call on page reload, logout, or after failed payment
  resetPayment: () =>
    set({
      checkoutStep: 'cart',
      preferenceId: null,
      paymentStatus: 'idle',
    }),
}))
