/**
 * OrderSummary — cart totals + checkout CTA.
 *
 * Uses granular Zustand selectors to avoid unnecessary re-renders.
 * CTA behavior:
 *   - Disabled when cart is empty
 *   - Authenticated: navigates to /checkout (future change)
 *   - Unauthenticated: navigates to /login with state { from: '/checkout' }
 *
 * Styling: Only semantic tokens — zero raw colors.
 */

import { Link } from 'react-router-dom'
import { useCartStore, useAuthStore } from '@/store'
import { formatCurrency } from '@/features/cart/types'

export function OrderSummary() {
  // Granular selectors — each re-renders only when its specific value changes
  const itemCount = useCartStore((s) => s.totalItems())
  const total = useCartStore((s) => s.totalPrice())
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const isEmpty = itemCount === 0

  const ctaTo = isAuthenticated ? '/checkout' : '/login'
  const ctaState = isAuthenticated ? undefined : { from: '/checkout' }

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

      {/* Total */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Total</span>
        <span className="text-xl font-bold text-foreground">
          {formatCurrency(total)}
        </span>
      </div>

      {/* CTA */}
      {isEmpty ? (
        <button
          type="button"
          disabled
          aria-disabled="true"
          className="w-full py-3 px-4 rounded-md bg-primary text-primary-foreground font-semibold text-base opacity-50 cursor-not-allowed"
        >
          Proceder al pago
        </button>
      ) : (
        <Link
          to={ctaTo}
          state={ctaState}
          className="block w-full py-3 px-4 rounded-md bg-primary text-primary-foreground font-semibold text-base text-center hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          Proceder al pago
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
