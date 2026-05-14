/**
 * OrderSummary — cart totals breakdown + checkout CTA.
 *
 * Uses granular Zustand selectors to avoid unnecessary re-renders.
 * CTA behavior:
 *   - Disabled when cart is empty
 *   - Authenticated: navigates to /checkout (future change)
 *   - Unauthenticated: navigates to /login with state { from: '/checkout' }
 *
 * Delivery logic:
 *   - FREE_DELIVERY_THRESHOLD and DELIVERY_FEE are local constants.
 *   - TODO: replace with API values in checkout change.
 *
 * Styling: Only semantic tokens — zero raw colors.
 */

import { Link } from 'react-router-dom'
import { useCartStore, useAuthStore } from '@/store'
import { formatCurrency } from '@/features/cart/types'

// TODO: replace with API values in checkout change
const FREE_DELIVERY_THRESHOLD = 3000
const DELIVERY_FEE = 500

export function OrderSummary() {
  // Granular selectors — each re-renders only when its specific value changes
  const itemCount = useCartStore((s) => s.totalItems())
  const subtotal = useCartStore((s) => s.totalPrice())
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const isEmpty = itemCount === 0

  const isFreeDelivery = subtotal >= FREE_DELIVERY_THRESHOLD
  const deliveryFee = isFreeDelivery ? 0 : DELIVERY_FEE
  const total = subtotal + deliveryFee
  const amountToFreeDelivery = FREE_DELIVERY_THRESHOLD - subtotal

  const ctaTo = isAuthenticated ? '/checkout' : '/login'
  // Login page expects { from: { pathname } } — same shape as ProtectedRoute
  const ctaState = isAuthenticated ? undefined : { from: { pathname: '/checkout' } }

  return (
    <aside
      aria-label="Resumen del pedido"
      className="bg-card border border-border rounded-lg p-6 space-y-4 sticky top-4"
    >
      <h2 className="text-lg font-semibold text-foreground border-b border-border pb-3">
        Resumen del pedido
      </h2>

      {/* Item count */}
      <p className="text-sm text-muted-foreground">
        {itemCount === 0
          ? 'No hay productos'
          : `${itemCount} producto${itemCount !== 1 ? 's' : ''}`}
      </p>

      {/* Cost breakdown */}
      <div className="space-y-2">
        {/* Subtotal row */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Subtotal</span>
          <span className="text-sm text-muted-foreground">
            {formatCurrency(subtotal)}
          </span>
        </div>

        {/* Delivery row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Envío</span>
            {isFreeDelivery && (
              <span
                aria-label="Envío gratis"
                className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20"
              >
                ¡Gratis!
              </span>
            )}
          </div>
          <span className="text-sm text-muted-foreground">
            {isFreeDelivery ? formatCurrency(0) : formatCurrency(DELIVERY_FEE)}
          </span>
        </div>

        {/* Progress bar — only shown when delivery is not yet free */}
        {!isEmpty && !isFreeDelivery && (
          <p className="text-xs text-muted-foreground mt-1">
            Te faltan{' '}
            <span className="font-medium text-foreground">
              {formatCurrency(amountToFreeDelivery)}
            </span>{' '}
            para envío gratis
          </p>
        )}

        {/* Divider */}
        <div className="border-t border-border pt-2 mt-2">
          {/* Total row — typographic hierarchy: largest, boldest */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">Total</span>
            <span className="text-xl font-bold text-foreground">
              {formatCurrency(total)}
            </span>
          </div>
        </div>
      </div>

      {/* CTA */}
      {isEmpty ? (
        <button
          type="button"
          disabled
          aria-disabled="true"
          className="w-full py-3.5 px-4 rounded-md bg-primary text-primary-foreground font-semibold text-base opacity-50 cursor-not-allowed"
        >
          Proceder al pago
        </button>
      ) : (
        <Link
          to={ctaTo}
          state={ctaState}
          className="block w-full py-3.5 px-4 rounded-md bg-primary text-primary-foreground font-semibold text-base text-center hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          Proceder al pago · {formatCurrency(total)}
        </Link>
      )}

      {/* Unauthenticated hint */}
      {!isAuthenticated && !isEmpty && (
        <p className="text-xs text-muted-foreground text-center">
          Deberás iniciar sesión para completar el pedido
        </p>
      )}
    </aside>
  )
}
