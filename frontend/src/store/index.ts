/**
 * Store Exports and Type Definitions
 * 
 * This is the single entry point for all store access.
 * Import hooks and types from here to maintain clean dependency management.
 * 
 * Usage:
 * ```typescript
 * import { useAuthStore, useCartStore, usePaymentStore, useUIStore } from '@/store'
 * import type { AuthStore, CartStore, PaymentStore, UIStore } from '@/store'
 * ```
 */

// Export store hooks
export { useAuthStore } from './authStore'
export { useCartStore } from './cartStore'
export { usePaymentStore } from './paymentStore'
export { useUIStore } from './uiStore'

// Export type definitions
export type {
  AuthStore,
  CartStore,
  CartItem,
  PaymentStore,
  UIStore,
} from './types'

// Re-export PaymentState (new checkout payment store shape)
export type { PaymentState } from '@/features/payments/types/payment.types'
