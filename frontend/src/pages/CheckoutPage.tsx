/**
 * CheckoutPage — full checkout flow integrating cart validation + payment.
 *
 * FSD layer: pages/ (consumes features/checkout + features/payments + store)
 *
 * Behavior:
 *   1. On mount, fires cart pre-validation mutation (useCheckoutValidation).
 *   2. Detects query params from MercadoPago redirect:
 *      ?payment=success|failure|pending&pedido_id=X → shows PaymentStatusModal.
 *   3. After validation passes (or user confirms soft warnings):
 *      - Shows buyer info form (nombre, email, telefono)
 *      - Shows PaymentMethodSelector
 *      - Shows pay button (MercadoPagoButton)
 *   4. On "Pagar": validates form → sets status → calls useCreateOrder →
 *      on success calls useCreatePreference → MercadoPagoButton opens modal.
 *   5. PaymentStatusModal shows when status is success | error | pending.
 *
 * Responsive:
 *   - Mobile (375px): single column, cart summary below form
 *   - Desktop (1280px): two columns (form left, cart summary right)
 *
 * Route: /checkout (requires CLIENT or ADMIN — see Router.tsx)
 */

import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useCheckoutValidation } from '@/features/checkout/hooks/useCheckoutValidation'
import { CheckoutValidationModal } from '@/features/checkout/components/CheckoutValidationModal'
import { PaymentMethodSelector } from '@/features/payments/components/PaymentMethodSelector'
import { MercadoPagoButton } from '@/features/payments/components/MercadoPagoButton'
import { PaymentStatusModal } from '@/features/payments/components/PaymentStatusModal'
import { useCreateOrder } from '@/features/payments/hooks/useCreateOrder'
import { useCreatePreference } from '@/features/payments/hooks/useCreatePreference'
import { usePaymentStore } from '@/store/paymentStore'
import { useCartStore } from '@/store/cartStore'
import { useUIStore } from '@/store/uiStore'
import { Spinner } from '@/shared/components/ui/Spinner'
import type { ValidarCarritoResponse } from '@/features/checkout/types'

// ---------------------------------------------------------------------------
// Buyer info form state
// ---------------------------------------------------------------------------

interface BuyerForm {
  nombre_comprador: string
  email_comprador: string
  telefono_comprador: string
}

interface FormErrors {
  nombre_comprador?: string
  email_comprador?: string
  telefono_comprador?: string
}

function validateForm(form: BuyerForm): FormErrors {
  const errors: FormErrors = {}

  if (!form.nombre_comprador.trim()) {
    errors.nombre_comprador = 'El nombre es obligatorio'
  } else if (form.nombre_comprador.trim().length < 3) {
    errors.nombre_comprador = 'El nombre debe tener al menos 3 caracteres'
  }

  if (!form.email_comprador.trim()) {
    errors.email_comprador = 'El email es obligatorio'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email_comprador)) {
    errors.email_comprador = 'Ingresá un email válido'
  }

  const telefonoDigits = form.telefono_comprador.replace(/\D/g, '')
  if (form.telefono_comprador.trim() && !/^\d{7,15}$/.test(telefonoDigits)) {
    errors.telefono_comprador = 'El teléfono debe contener entre 7 y 15 dígitos (solo números)'
  }

  return errors
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function CheckoutPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Cart store
  const items = useCartStore((state) => state.items)
  const totalPrice = useCartStore((state) => state.totalPrice)

  // Payment store
  const setStatus = usePaymentStore((state) => state.setStatus)
  const setPedidoId = usePaymentStore((state) => state.setPedidoId)
  const paymentMethod = usePaymentStore((state) => state.method)
  const paymentStatus = usePaymentStore((state) => state.status)
  const preferenceId = usePaymentStore((state) => state.preferenceId)

  // Toast
  const addToast = useUIStore((state) => state.addToast)

  // UI drawer control (BUG 3 fix)
  const setCartDrawerOpen = useUIStore((state) => state.setCartDrawerOpen)

  // Cart validation
  const { mutate: validateCart, isPending: isValidating, data: validationData, isError: isValidationError } = useCheckoutValidation()

  // Order + preference creation
  const createOrderMutation = useCreateOrder()
  const createPreferenceMutation = useCreatePreference()

  // Local form state
  const [form, setForm] = useState<BuyerForm>({
    nombre_comprador: '',
    email_comprador: '',
    telefono_comprador: '',
  })
  const [formErrors, setFormErrors] = useState<FormErrors>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [confirmedDespiteWarnings, setConfirmedDespiteWarnings] = useState(false)

  // ---------------------------------------------------------------------------
  // BUG 3 fix: close CartDrawer on checkout mount
  // ---------------------------------------------------------------------------
  useEffect(() => {
    setCartDrawerOpen(false)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------------------------------------------------------------------
  // 6.6 — Detect query params from MercadoPago redirect
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const paymentResult = searchParams.get('payment')
    const pedidoIdParam = searchParams.get('pedido_id')

    if (paymentResult === 'success' && pedidoIdParam) {
      const id = parseInt(pedidoIdParam, 10)
      if (!isNaN(id)) {
        setPedidoId(id)
        setStatus('success')
      }
    } else if (paymentResult === 'failure') {
      if (pedidoIdParam) {
        const id = parseInt(pedidoIdParam, 10)
        if (!isNaN(id)) setPedidoId(id)
      }
      setStatus('error')
    } else if (paymentResult === 'pending') {
      if (pedidoIdParam) {
        const id = parseInt(pedidoIdParam, 10)
        if (!isNaN(id)) setPedidoId(id)
      }
      setStatus('pending')
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------------------------------------------------------------------
  // Validate cart on mount (if no payment result from query params)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const paymentResult = searchParams.get('payment')
    if (paymentResult) return // Skip validation if coming back from MP

    // Redirect if cart is empty
    if (items.length === 0) {
      addToast({ message: 'Tu carrito está vacío', type: 'info' })
      navigate('/')
      return
    }

    validateCart()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Open validation modal when issues detected
  useEffect(() => {
    if (!validationData) return
    const result = validationData as ValidarCarritoResponse
    const isHardBlock =
      result.carrito_vacio ||
      result.sin_direccion ||
      result.productos_invalidos.length > 0
    const hasWarnings =
      result.stock_insuficiente.length > 0 || result.cambios_de_precio.length > 0

    if ((isHardBlock || hasWarnings) && !confirmedDespiteWarnings) {
      setModalOpen(true)
    }
  }, [validationData, confirmedDespiteWarnings])

  // ---------------------------------------------------------------------------
  // 6.5 — Pay button handler
  // ---------------------------------------------------------------------------
  function handlePay() {
    const errors = validateForm(form)
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }

    setFormErrors({})
    setStatus('creating_order')

    // Build order payload from cart
    createOrderMutation.mutate(
      {
        direccion_entrega_id: 1, // TODO: pick from address selector when available
        forma_pago_id: 1,        // MercadoPago = 1 (verify with backend seed)
        observacion: undefined,
        items: items.map((item) => ({
          producto_id: Number(item.productId),
          cantidad: item.quantity,
          ingredientes_excluidos: item.ingredientes_excluidos,
        })),
      },
      {
        onSuccess: (orderData) => {
          // createPreference is triggered inside useCreateOrder via onSuccess,
          // but we also need it here to open the MP modal after preference is ready
          createPreferenceMutation.mutate(
            { pedido_id: orderData.id },
            {
              onError: (err) => {
                console.error('[CheckoutPage] createPreference failed:', err)
                setStatus('idle')
                addToast({
                  message: 'No se pudo generar el pago. Intentá nuevamente.',
                  type: 'error',
                })
              },
            },
          )
        },
        onError: (err) => {
          console.error('[CheckoutPage] createOrder failed:', err)
          setStatus('idle')
          addToast({
            message: 'No se pudo crear el pedido. Revisá tus datos e intentá nuevamente.',
            type: 'error',
          })
        },
      },
    )
  }

  // ---------------------------------------------------------------------------
  // Derived flags
  // ---------------------------------------------------------------------------
  const isValidationLoading = isValidating
  const validationResult = validationData as ValidarCarritoResponse | undefined
  const isHardBlock = validationResult
    ? validationResult.carrito_vacio ||
      validationResult.sin_direccion ||
      validationResult.productos_invalidos.length > 0
    : false

  // Show form when validation passed or user confirmed
  const showForm =
    !modalOpen &&
    (confirmedDespiteWarnings || (!isHardBlock && !!validationResult)) &&
    !searchParams.get('payment')

  const cartTotal = totalPrice()
  const isPayButtonLoading =
    paymentStatus === 'creating_order' || paymentStatus === 'creating_preference'

  // ---------------------------------------------------------------------------
  // Loading state (validating cart)
  // ---------------------------------------------------------------------------
  if (isValidationLoading) {
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

  // Validation network error
  if (isValidationError && !validationData) {
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
            onClick={() => validateCart()}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
          >
            Reintentar
          </button>
        </div>
      </main>
    )
  }

  return (
    <main
      aria-label="Checkout"
      className="mx-auto max-w-screen-xl px-4 sm:px-6 lg:px-8 py-8"
    >
      {/* Validation modal (hard blocks + soft warnings) */}
      <CheckoutValidationModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false)
          if (isHardBlock) navigate('/cart')
        }}
        onConfirm={() => {
          setConfirmedDespiteWarnings(true)
          setModalOpen(false)
        }}
        validationResult={validationResult}
      />

      {/* Payment status modal (success | error | pending) */}
      <PaymentStatusModal />

      {/* Checkout form — two columns on desktop, single on mobile */}
      {showForm && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-8">
          {/* ── Left column: form + payment method ─────────────── */}
          <div className="space-y-8">
            {/* BUG 3 fix: back to cart button */}
            <button
              type="button"
              onClick={() => navigate('/cart')}
              className="mb-4 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Volver al carrito
            </button>

            <h1 className="text-2xl font-bold text-foreground">
              Finalizar pedido
            </h1>

            {/* Buyer info form */}
            <section
              aria-labelledby="buyer-form-heading"
              className="rounded-xl border border-border bg-card p-6"
            >
              <h2
                id="buyer-form-heading"
                className="text-lg font-semibold text-foreground mb-4"
              >
                Datos del comprador
              </h2>

              <div className="space-y-4">
                {/* Nombre */}
                <div>
                  <label
                    htmlFor="nombre_comprador"
                    className="block text-sm font-medium text-foreground mb-1"
                  >
                    Nombre completo <span aria-hidden="true">*</span>
                  </label>
                  <input
                    id="nombre_comprador"
                    type="text"
                    value={form.nombre_comprador}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        nombre_comprador: e.target.value,
                      }))
                    }
                    aria-required="true"
                    aria-invalid={!!formErrors.nombre_comprador}
                    aria-describedby={
                      formErrors.nombre_comprador
                        ? 'nombre-error'
                        : undefined
                    }
                    placeholder="Ej: Juan Pérez"
                    className={[
                      'w-full rounded-lg border px-3 py-2 text-sm bg-background text-foreground placeholder:text-muted-foreground',
                      'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                      formErrors.nombre_comprador
                        ? 'border-destructive focus:ring-destructive'
                        : 'border-border',
                    ].join(' ')}
                  />
                  {formErrors.nombre_comprador && (
                    <p
                      id="nombre-error"
                      role="alert"
                      className="mt-1 text-xs text-destructive"
                    >
                      {formErrors.nombre_comprador}
                    </p>
                  )}
                </div>

                {/* Email */}
                <div>
                  <label
                    htmlFor="email_comprador"
                    className="block text-sm font-medium text-foreground mb-1"
                  >
                    Email <span aria-hidden="true">*</span>
                  </label>
                  <input
                    id="email_comprador"
                    type="email"
                    value={form.email_comprador}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        email_comprador: e.target.value,
                      }))
                    }
                    aria-required="true"
                    aria-invalid={!!formErrors.email_comprador}
                    aria-describedby={
                      formErrors.email_comprador ? 'email-error' : undefined
                    }
                    placeholder="Ej: juan@example.com"
                    className={[
                      'w-full rounded-lg border px-3 py-2 text-sm bg-background text-foreground placeholder:text-muted-foreground',
                      'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                      formErrors.email_comprador
                        ? 'border-destructive focus:ring-destructive'
                        : 'border-border',
                    ].join(' ')}
                  />
                  {formErrors.email_comprador && (
                    <p
                      id="email-error"
                      role="alert"
                      className="mt-1 text-xs text-destructive"
                    >
                      {formErrors.email_comprador}
                    </p>
                  )}
                </div>

                {/* Teléfono (optional) */}
                <div>
                  <label
                    htmlFor="telefono_comprador"
                    className="block text-sm font-medium text-foreground mb-1"
                  >
                    Teléfono{' '}
                    <span className="text-muted-foreground text-xs">
                      (opcional)
                    </span>
                  </label>
                  <input
                    id="telefono_comprador"
                    type="tel"
                    value={form.telefono_comprador}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        telefono_comprador: e.target.value,
                      }))
                    }
                    aria-invalid={!!formErrors.telefono_comprador}
                    aria-describedby={
                      formErrors.telefono_comprador
                        ? 'telefono-error'
                        : undefined
                    }
                    placeholder="Ej: 1123456789"
                    className={[
                      'w-full rounded-lg border px-3 py-2 text-sm bg-background text-foreground placeholder:text-muted-foreground',
                      'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                      formErrors.telefono_comprador
                        ? 'border-destructive focus:ring-destructive'
                        : 'border-border',
                    ].join(' ')}
                  />
                  {formErrors.telefono_comprador && (
                    <p
                      id="telefono-error"
                      role="alert"
                      className="mt-1 text-xs text-destructive"
                    >
                      {formErrors.telefono_comprador}
                    </p>
                  )}
                </div>
              </div>
            </section>

            {/* Payment method selector */}
            <section
              aria-labelledby="payment-method-heading"
              className="rounded-xl border border-border bg-card p-6"
            >
              <h2
                id="payment-method-heading"
                className="text-lg font-semibold text-foreground mb-4"
              >
                Método de pago
              </h2>
              <PaymentMethodSelector />
            </section>

            {/* Pay button — only show when method is selected */}
            {paymentMethod && (
              <div>
                {paymentMethod === 'mercadopago' ? (
                  <>
                    {/* Step 1: no preference yet — show "Preparar pago" only */}
                    {!preferenceId && (
                      <button
                        type="button"
                        onClick={handlePay}
                        disabled={isPayButtonLoading}
                        data-testid="generate-preference-btn"
                        className="w-full rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isPayButtonLoading ? 'Preparando pago...' : 'Preparar pago'}
                      </button>
                    )}

                    {/* Step 2: preference ready — show "Pagar con MercadoPago" only */}
                    {preferenceId && <MercadoPagoButton />}
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={handlePay}
                    disabled={isPayButtonLoading}
                    className="w-full rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Confirmar pedido
                  </button>
                )}
              </div>
            )}
          </div>

          {/* ── Right column: cart summary ──────────────────────── */}
          <aside
            aria-label="Resumen del carrito"
            className="rounded-xl border border-border bg-card p-6 h-fit lg:sticky lg:top-8"
          >
            <h2 className="text-lg font-semibold text-foreground mb-4">
              Tu pedido
            </h2>

            {/* Items */}
            <ul className="space-y-3 mb-4">
              {items.map((item) => (
                <li
                  key={item.productId}
                  className="flex items-start justify-between gap-2 text-sm"
                >
                  <div className="flex-1 min-w-0">
                    <span className="font-medium text-foreground">
                      {item.name}
                    </span>
                    <span className="ml-1 text-muted-foreground">
                      x{item.quantity}
                    </span>
                  </div>
                  <span className="shrink-0 font-medium text-foreground">
                    ${(item.price * item.quantity).toFixed(2)}
                  </span>
                </li>
              ))}
            </ul>

            {/* Divider */}
            <div className="border-t border-border pt-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="text-foreground">${cartTotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-base">
                <span className="text-foreground">Total</span>
                <span className="text-foreground">${cartTotal.toFixed(2)}</span>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Coming back from MP but no payment param — just show form */}
      {!showForm && !isValidationLoading && !modalOpen && !searchParams.get('payment') && validationResult && isHardBlock && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            Revisá tu carrito para continuar.
          </p>
          <button
            onClick={() => navigate('/cart')}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
          >
            Ir al carrito
          </button>
        </div>
      )}
    </main>
  )
}
