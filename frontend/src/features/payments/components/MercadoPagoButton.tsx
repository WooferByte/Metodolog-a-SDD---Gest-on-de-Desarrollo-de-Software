/**
 * MercadoPagoButton — button to initiate the MercadoPago checkout modal.
 *
 * Uses the brickless flow:
 *   new window.MercadoPago(publicKey, { locale: 'es-AR' })
 *   mp.checkout({ preference: { id: preferenceId }, autoOpen: true })
 *
 * States:
 *   - idle with preferenceId: enabled, shows "Pagar con MercadoPago"
 *   - creating_order | creating_preference: loading spinner, disabled
 *   - SDK not available: disabled with error message
 *   - no preferenceId yet: disabled (waiting for preference creation)
 *
 * The SDK is loaded via CDN in index.html with defer.
 * Availability verified via typeof window.MercadoPago !== 'undefined'.
 */

import { useRef, useEffect, useState } from 'react'
import { usePaymentStore } from '@/store/paymentStore'

interface MercadoPagoButtonProps {
  /** Called when the MP checkout is initiated */
  onCheckoutOpen?: () => void
}

export function MercadoPagoButton({ onCheckoutOpen }: MercadoPagoButtonProps) {
  const preferenceId = usePaymentStore((state) => state.preferenceId)
  const status = usePaymentStore((state) => state.status)
  const setStatus = usePaymentStore((state) => state.setStatus)

  const [sdkAvailable, setSdkAvailable] = useState(false)
  const [sdkError, setSdkError] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mpInstanceRef = useRef<any>(null)

  // Check SDK availability and initialize after mount
  useEffect(() => {
    if (typeof window.MercadoPago === 'undefined') {
      setSdkError(true)
      return
    }

    setSdkAvailable(true)

    // Initialize MP instance with the public key from env (or test placeholder)
    const publicKey = import.meta.env.VITE_MP_PUBLIC_KEY || 'TEST-key'
    try {
      mpInstanceRef.current = new window.MercadoPago(publicKey, {
        locale: 'es-AR',
      })
    } catch (err) {
      console.error('[MercadoPagoButton] Failed to initialize SDK:', err)
      setSdkError(true)
      setSdkAvailable(false)
    }

    // Cleanup: clear instance reference on unmount
    return () => {
      mpInstanceRef.current = null
    }
  }, [])

  const isLoading =
    status === 'creating_order' || status === 'creating_preference'

  const isDisabled =
    !sdkAvailable ||
    sdkError ||
    !preferenceId ||
    isLoading ||
    status === 'waiting_payment'

  function handleClick() {
    if (isDisabled || !mpInstanceRef.current || !preferenceId) return

    try {
      mpInstanceRef.current.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      })
      setStatus('waiting_payment')
      onCheckoutOpen?.()
    } catch (err) {
      console.error('[MercadoPagoButton] checkout() failed:', err)
      setStatus('error')
    }
  }

  if (sdkError) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
      >
        El procesador de pagos no está disponible. Por favor, recargá la
        página e intentá nuevamente.
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isDisabled}
      aria-busy={isLoading}
      aria-disabled={isDisabled}
      data-testid="mercadopago-button"
      className={[
        'relative flex w-full items-center justify-center gap-2 rounded-lg px-6 py-3',
        'text-sm font-semibold transition-colors focus-visible:outline-none',
        'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        isDisabled
          ? 'cursor-not-allowed bg-muted text-muted-foreground'
          : 'bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/80',
      ].join(' ')}
    >
      {isLoading ? (
        <>
          {/* Spinner */}
          <svg
            className="h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <span>
            {status === 'creating_order'
              ? 'Creando pedido...'
              : 'Generando pago...'}
          </span>
        </>
      ) : (
        <>
          <span aria-hidden="true">💳</span>
          <span>
            {status === 'waiting_payment'
              ? 'Procesando pago...'
              : 'Pagar con MercadoPago'}
          </span>
        </>
      )}
    </button>
  )
}
