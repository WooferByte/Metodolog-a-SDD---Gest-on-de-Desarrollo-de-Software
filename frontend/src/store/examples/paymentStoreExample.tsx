/**
 * Example: PaymentStore Usage
 * 
 * Demonstrates how to use the paymentStore to manage the checkout workflow
 * and payment process with MercadoPago integration.
 */

import { usePaymentStore } from '@/store'

/**
 * CheckoutWizard Component
 * 
 * Shows how to:
 * - Initialize checkout workflow
 * - Display current step
 * - Set MercadoPago preference
 * - Track payment status
 * - Handle payment completion/failure
 */
export function CheckoutWizardExample() {
  const checkoutStep = usePaymentStore((state) => state.checkoutStep)
  const paymentStatus = usePaymentStore((state) => state.paymentStatus)
  const preferenceId = usePaymentStore((state) => state.preferenceId)
  const startCheckout = usePaymentStore((state) => state.startCheckout)
  const setPreference = usePaymentStore((state) => state.setPreference)
  const updatePaymentStatus = usePaymentStore(
    (state) => state.updatePaymentStatus,
  )
  const resetPayment = usePaymentStore((state) => state.resetPayment)

  const handleCheckout = () => {
    startCheckout()
  }

  const handleCreatePreference = () => {
    // In real app: Call MercadoPago API to create preference
    // Simulating API response with preference ID
    setPreference('mp-pref-123456')
  }

  const handleRetry = () => {
    resetPayment()
    startCheckout()
  }

  return (
    <div>
      <h2>Checkout Process</h2>

      <p>Current Step: {checkoutStep}</p>
      <p>Status: {paymentStatus}</p>

      {checkoutStep === 'cart' && (
        <button onClick={handleCheckout}>Start Checkout</button>
      )}

      {checkoutStep === 'shipping' && (
        <div>
          <p>Please enter shipping details...</p>
          <button onClick={handleCreatePreference}>
            Proceed to Payment
          </button>
        </div>
      )}

      {checkoutStep === 'payment' && (
        <div>
          <p>Payment preference created: {preferenceId}</p>
          {paymentStatus === 'idle' && (
            <button onClick={() => updatePaymentStatus('processing')}>
              Process Payment
            </button>
          )}
          {paymentStatus === 'processing' && <p>Processing payment...</p>}
          {paymentStatus === 'completed' && (
            <p>Payment successful! Your order is confirmed.</p>
          )}
          {paymentStatus === 'failed' && (
            <div>
              <p>Payment failed. Please try again.</p>
              <button onClick={handleRetry}>Retry</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * PaymentStatus Component
 * 
 * Shows how to:
 * - Display payment status
 * - Show different UI based on payment state
 * - Handle user interactions during payment
 */
export function PaymentStatusExample() {
  const paymentStatus = usePaymentStore((state) => state.paymentStatus)
  const resetPayment = usePaymentStore((state) => state.resetPayment)

  return (
    <div>
      <h3>Payment Status</h3>
      {paymentStatus === 'idle' && <p>Ready to start payment</p>}
      {paymentStatus === 'processing' && <p>Processing...</p>}
      {paymentStatus === 'completed' && <p>Payment Complete!</p>}
      {paymentStatus === 'failed' && (
        <div>
          <p>Payment Failed</p>
          <button onClick={resetPayment}>Start Over</button>
        </div>
      )}
    </div>
  )
}
