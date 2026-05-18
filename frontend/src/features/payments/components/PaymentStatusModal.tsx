/**
 * PaymentStatusModal — WCAG AA modal showing the payment result.
 *
 * Shown when paymentStore.status is 'success', 'error', or 'pending'.
 *
 * Three modes:
 *   success: green check, "¡Pago exitoso!", "Ver mi pedido" → /orders/{pedidoId}
 *   error: red X, "El pago no pudo procesarse", "Intentar de nuevo" + "Cancelar"
 *   pending: clock icon, "Tu pago está siendo procesado", "Ver mis pedidos"
 *
 * Accessibility:
 *   - role="dialog" aria-modal="true"
 *   - aria-labelledby pointing to the modal title
 *   - Focus trapped inside modal via native <dialog> element
 *   - Closeable with Escape key (native dialog behavior)
 *
 * Uses native <dialog> element for built-in focus trap and Escape key handling.
 */

import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePaymentStore } from '@/store/paymentStore'
import { useCartStore } from '@/store/cartStore'
import { useCreatePreference } from '../hooks/useCreatePreference'

export function PaymentStatusModal() {
  const status = usePaymentStore((state) => state.status)
  const pedidoId = usePaymentStore((state) => state.pedidoId)
  const reset = usePaymentStore((state) => state.reset)
  const clearCart = useCartStore((state) => state.clearCart)
  const navigate = useNavigate()

  const { mutate: createPreference } = useCreatePreference()

  const dialogRef = useRef<HTMLDialogElement>(null)
  const isVisible = status === 'success' || status === 'error' || status === 'pending'

  const titleId = 'payment-status-modal-title'

  // Open/close native dialog
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (isVisible) {
      if (!dialog.open) {
        try {
          dialog.showModal()
        } catch {
          // jsdom: showModal may not be available
        }
      }
    } else {
      if (dialog.open) {
        try {
          dialog.close()
        } catch {
          // jsdom: close may not be available
        }
      }
    }
  }, [isVisible])

  function handleViewOrder() {
    if (pedidoId) {
      navigate(`/pedidos/${pedidoId}`)
    }
    reset()
    clearCart()
  }

  function handleViewOrders() {
    navigate('/orders')
  }

  function handleRetry() {
    if (pedidoId) {
      // Create a new preference for the same pedido_id (don't create new order)
      createPreference({ pedido_id: pedidoId })
    }
  }

  function handleCancel() {
    reset()
    navigate('/')
  }

  if (!isVisible) return null

  return (
    <dialog
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      data-testid="payment-status-modal"
      className={[
        'fixed inset-0 z-50 m-auto max-w-md rounded-xl border border-border bg-card p-6 shadow-xl',
        'w-[calc(100%-2rem)] sm:w-full',
        'backdrop:bg-foreground/30 backdrop:backdrop-blur-sm',
      ].join(' ')}
      onKeyDown={(e) => {
        if (e.key === 'Escape') {
          if (status === 'error') handleCancel()
        }
      }}
    >
      {/* ── Success ─────────────────────────────────────────────── */}
      {status === 'success' && (
        <div className="flex flex-col items-center gap-4 text-center">
          <div
            aria-hidden="true"
            className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-green-600"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-9 w-9"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>

          <h2
            id={titleId}
            className="text-xl font-bold text-foreground"
          >
            ¡Pago exitoso!
          </h2>
          <p className="text-sm text-muted-foreground">
            Tu pedido #{pedidoId} fue procesado correctamente.
          </p>

          <button
            type="button"
            onClick={handleViewOrder}
            data-testid="modal-view-order-btn"
            className="mt-2 w-full rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Ver mi pedido
          </button>
        </div>
      )}

      {/* ── Error ───────────────────────────────────────────────── */}
      {status === 'error' && (
        <div className="flex flex-col items-center gap-4 text-center">
          <div
            aria-hidden="true"
            className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10 text-destructive"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-9 w-9"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>

          <h2
            id={titleId}
            className="text-xl font-bold text-foreground"
          >
            El pago no pudo procesarse
          </h2>
          <p className="text-sm text-muted-foreground">
            Ocurrió un problema al procesar tu pago. Podés intentar nuevamente.
          </p>

          <div className="mt-2 flex w-full flex-col gap-2">
            <button
              type="button"
              onClick={handleRetry}
              data-testid="modal-retry-btn"
              className="w-full rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              Intentar de nuevo
            </button>
            <button
              type="button"
              onClick={handleCancel}
              data-testid="modal-cancel-btn"
              className="w-full rounded-lg border border-border bg-background px-6 py-3 text-sm font-semibold text-foreground hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* ── Pending ─────────────────────────────────────────────── */}
      {status === 'pending' && (
        <div className="flex flex-col items-center gap-4 text-center">
          <div
            aria-hidden="true"
            className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 text-amber-600"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-9 w-9"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          <h2
            id={titleId}
            className="text-xl font-bold text-foreground"
          >
            Pago en proceso
          </h2>
          <p className="text-sm text-muted-foreground">
            Tu pago está siendo procesado. Te notificaremos cuando se confirme.
          </p>

          <button
            type="button"
            onClick={handleViewOrders}
            data-testid="modal-view-orders-btn"
            className="mt-2 w-full rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Ver mis pedidos
          </button>
        </div>
      )}
    </dialog>
  )
}
