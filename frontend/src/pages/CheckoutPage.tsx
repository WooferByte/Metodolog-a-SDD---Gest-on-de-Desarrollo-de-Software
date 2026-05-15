/**
 * CheckoutPage — entry point for the checkout flow.
 *
 * FSD layer: pages/ (consumes features/checkout)
 *
 * Behavior (from spec checkout-validation-ui):
 *   1. On mount, fires the cart validation mutation once (useEffect + mutate).
 *   2. While the validation is pending: shows a loading spinner/skeleton.
 *   3. When validation data is available:
 *      a. Hard block (empty cart, no address, or invalid products):
 *         Show CheckoutValidationModal — user cannot proceed.
 *      b. Soft warning (stock / price issues):
 *         Show CheckoutValidationModal — user can choose to proceed anyway.
 *      c. Clean validation:
 *         Render the checkout form directly (no modal).
 *
 * The checkout form itself is a placeholder — the actual order creation form
 * will be implemented in the orders-fsm-backend + frontend-checkout changes.
 *
 * Route: /checkout (requires CLIENT or ADMIN, defined in Router.tsx)
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCheckoutValidation } from '@/features/checkout/hooks/useCheckoutValidation'
import { CheckoutValidationModal } from '@/features/checkout/components/CheckoutValidationModal'
import { Spinner } from '@/shared/components/ui/Spinner'
import type { ValidarCarritoResponse } from '@/features/checkout/types'

export default function CheckoutPage() {
  const navigate = useNavigate()
  const { mutate, isPending, data, isError } = useCheckoutValidation()

  // Modal open state — open automatically when validation data arrives with issues
  const [modalOpen, setModalOpen] = useState(false)
  // Whether the user confirmed through a soft warning and wants to proceed
  const [confirmedDespiteWarnings, setConfirmedDespiteWarnings] = useState(false)

  // 10.3 — Trigger validation on mount, once
  useEffect(() => {
    mutate()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // 10.5–10.6 — Open modal when data arrives with issues
  useEffect(() => {
    if (!data) return

    const result = data as ValidarCarritoResponse
    const isHardBlock = result.carrito_vacio || result.sin_direccion || result.productos_invalidos.length > 0
    const hasWarnings =
      result.stock_insuficiente.length > 0 || result.cambios_de_precio.length > 0

    if ((isHardBlock || hasWarnings) && !confirmedDespiteWarnings) {
      setModalOpen(true)
    }
  }, [data, confirmedDespiteWarnings])

  // 10.4 — Loading state
  if (isPending) {
    return (
      <main
        aria-label="Validando carrito..."
        className="flex min-h-[60vh] items-center justify-center"
      >
        <div className="flex flex-col items-center gap-4">
          <Spinner />
          <p className="text-sm text-muted-foreground">
            Verificando disponibilidad de productos...
          </p>
        </div>
      </main>
    )
  }

  // Network/unexpected error state
  if (isError && !data) {
    return (
      <main
        aria-label="Error al validar"
        className="flex min-h-[60vh] items-center justify-center"
      >
        <div className="text-center">
          <p className="text-destructive font-medium">
            No se pudo validar el carrito. Intentá nuevamente.
          </p>
          <button
            onClick={() => mutate()}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
          >
            Reintentar
          </button>
        </div>
      </main>
    )
  }

  const validationResult = data as ValidarCarritoResponse | undefined

  // 10.5 — Calculate flags for current data
  const isHardBlock = validationResult
    ? validationResult.carrito_vacio ||
      validationResult.sin_direccion ||
      validationResult.productos_invalidos.length > 0
    : false

  // 10.7 — If validation is clean (or user confirmed past warnings), show the form
  const showForm = !modalOpen && (confirmedDespiteWarnings || (!isHardBlock && !!validationResult))

  return (
    <main
      aria-label="Checkout"
      className="max-w-screen-lg mx-auto px-4 sm:px-6 lg:px-8 py-8"
    >
      {/* Validation modal — shown for hard blocks AND soft warnings */}
      <CheckoutValidationModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false)
          // Hard block: go back to cart on close
          if (isHardBlock) {
            navigate('/cart')
          }
        }}
        onConfirm={() => {
          // Soft warning confirmed — user accepts and wants to proceed
          setConfirmedDespiteWarnings(true)
          setModalOpen(false)
        }}
        validationResult={validationResult}
      />

      {/* Checkout form — rendered when validation passed (or user confirmed) */}
      {showForm && (
        <section>
          <h1 className="text-2xl font-bold text-foreground mb-6">
            Finalizar pedido
          </h1>

          {/* Placeholder checkout form — full implementation in orders-fsm-backend */}
          <div className="rounded-xl border border-border bg-card p-6">
            <p className="text-muted-foreground text-sm">
              El formulario de pedido estará disponible próximamente.
              La validación del carrito fue exitosa.
            </p>
          </div>
        </section>
      )}
    </main>
  )
}
