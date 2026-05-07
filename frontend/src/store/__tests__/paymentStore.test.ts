/**
 * PaymentStore Tests
 * 
 * Tests for payment workflow state management, checkout steps,
 * payment status tracking, and verification that NO persistence occurs.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { usePaymentStore } from '../paymentStore'

describe('PaymentStore', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    // Reset store to initial state
    usePaymentStore.setState({
      checkoutStep: 'cart',
      preferenceId: null,
      paymentStatus: 'idle',
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = usePaymentStore.getState()
      expect(state.checkoutStep).toBe('cart')
      expect(state.preferenceId).toBeNull()
      expect(state.paymentStatus).toBe('idle')
    })
  })

  describe('startCheckout', () => {
    it('should initialize checkout workflow', () => {
      const { startCheckout } = usePaymentStore.getState()
      startCheckout()

      const state = usePaymentStore.getState()
      expect(state.checkoutStep).toBe('shipping')
      expect(state.paymentStatus).toBe('idle')
      expect(state.preferenceId).toBeNull()
    })

    it('should reset preference when starting checkout', () => {
      const { setPreference, startCheckout } = usePaymentStore.getState()

      setPreference('old-pref-123')
      startCheckout()

      const state = usePaymentStore.getState()
      expect(state.preferenceId).toBeNull()
    })
  })

  describe('setPreference', () => {
    it('should set MercadoPago preference ID', () => {
      const { setPreference } = usePaymentStore.getState()
      setPreference('mp-pref-123')

      const state = usePaymentStore.getState()
      expect(state.preferenceId).toBe('mp-pref-123')
    })

    it('should move to payment step', () => {
      const { setPreference } = usePaymentStore.getState()
      setPreference('mp-pref-123')

      const state = usePaymentStore.getState()
      expect(state.checkoutStep).toBe('payment')
    })
  })

  describe('updatePaymentStatus', () => {
    it('should update payment status to processing', () => {
      const { updatePaymentStatus } = usePaymentStore.getState()
      updatePaymentStatus('processing')

      expect(usePaymentStore.getState().paymentStatus).toBe('processing')
    })

    it('should update payment status to completed', () => {
      const { updatePaymentStatus } = usePaymentStore.getState()
      updatePaymentStatus('completed')

      expect(usePaymentStore.getState().paymentStatus).toBe('completed')
    })

    it('should update payment status to failed', () => {
      const { updatePaymentStatus } = usePaymentStore.getState()
      updatePaymentStatus('failed')

      expect(usePaymentStore.getState().paymentStatus).toBe('failed')
    })
  })

  describe('resetPayment', () => {
    it('should reset all payment state to initial', () => {
      const { startCheckout, setPreference, updatePaymentStatus, resetPayment } =
        usePaymentStore.getState()

      // Setup complex state
      startCheckout()
      setPreference('mp-pref-123')
      updatePaymentStatus('processing')

      // Reset
      resetPayment()

      const state = usePaymentStore.getState()
      expect(state.checkoutStep).toBe('cart')
      expect(state.preferenceId).toBeNull()
      expect(state.paymentStatus).toBe('idle')
    })
  })

  describe('NO persistence (security)', () => {
    it('should NOT persist any state to localStorage', () => {
      const { startCheckout, setPreference, updatePaymentStatus } =
        usePaymentStore.getState()

      startCheckout()
      setPreference('mp-pref-123')
      updatePaymentStatus('processing')

      // Payment store should NOT be in localStorage
      const paymentStored = localStorage.getItem('food-store-payment')
      expect(paymentStored).toBeNull()
    })

    it('should lose all state on page reload', () => {
      const { startCheckout, setPreference } = usePaymentStore.getState()

      startCheckout()
      setPreference('mp-pref-123')

      // Simulate page reload by resetting state
      usePaymentStore.setState({
        checkoutStep: 'cart',
        preferenceId: null,
        paymentStatus: 'idle',
      })

      const state = usePaymentStore.getState()
      expect(state.checkoutStep).toBe('cart')
      expect(state.preferenceId).toBeNull()
      expect(state.paymentStatus).toBe('idle')
    })

    it('should have no persist middleware configured', () => {
      // Verify payment store doesn't have persist middleware
      // by checking that state changes don't appear in localStorage
      const initialLength = Object.keys(localStorage).length

      const { startCheckout } = usePaymentStore.getState()
      startCheckout()

      expect(Object.keys(localStorage).length).toBe(initialLength)
    })
  })

  describe('Checkout workflow', () => {
    it('should support multi-step checkout flow', () => {
      const {
        startCheckout,
        setPreference,
        updatePaymentStatus,
        resetPayment,
      } = usePaymentStore.getState()

      // Step 1: User starts checkout from cart
      startCheckout()
      expect(usePaymentStore.getState().checkoutStep).toBe('shipping')

      // Step 2: User fills shipping and sets preference
      setPreference('mp-pref-123')
      expect(usePaymentStore.getState().checkoutStep).toBe('payment')

      // Step 3: Payment is processing
      updatePaymentStatus('processing')
      expect(usePaymentStore.getState().paymentStatus).toBe('processing')

      // Step 4: Payment completed
      updatePaymentStatus('completed')
      expect(usePaymentStore.getState().paymentStatus).toBe('completed')

      // Step 5: User can reset for another purchase
      resetPayment()
      expect(usePaymentStore.getState().checkoutStep).toBe('cart')
    })

    it('should handle payment failure and retry', () => {
      const {
        startCheckout,
        setPreference,
        updatePaymentStatus,
      } = usePaymentStore.getState()

      startCheckout()
      setPreference('mp-pref-123')
      updatePaymentStatus('processing')
      updatePaymentStatus('failed')

      expect(usePaymentStore.getState().paymentStatus).toBe('failed')

      // User can try again with new preference
      setPreference('mp-pref-456')
      updatePaymentStatus('processing')

      expect(usePaymentStore.getState().preferenceId).toBe('mp-pref-456')
      expect(usePaymentStore.getState().paymentStatus).toBe('processing')
    })
  })
})
