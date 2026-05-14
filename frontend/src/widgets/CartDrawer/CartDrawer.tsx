/**
 * CartDrawer — slide-in drawer from the right side.
 *
 * Trigger: CartIcon in Navbar (via useUIStore.cartDrawerOpen flag).
 * Content: Scrollable list of CartItemRow + fixed footer with OrderSummary.
 *
 * Accessibility (WCAG 2.1 AA):
 *   - role="dialog" aria-modal="true" aria-label="Carrito de compras"
 *   - Focus trap: focus moves to close button on open; returns to trigger on close
 *   - Escape key closes the drawer
 *   - Backdrop click closes the drawer
 *   - aria-live on item count in header
 *
 * Animation: CSS translate + transition (Tailwind v4 classes)
 *   - Closed: translate-x-full (off-screen right)
 *   - Open:   translate-x-0 (visible)
 *
 * Responsive: full-screen on mobile, 420px fixed on sm+
 *
 * Styling: Only semantic tokens — zero raw colors.
 */

import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { X, ShoppingCart } from 'lucide-react'
import { useUIStore, useCartStore, useAuthStore } from '@/store'
import { CartItemRow } from '@/features/cart/components/CartItemRow'
import { EmptyCart } from '@/features/cart/components/EmptyCart'
import { formatCurrency } from '@/features/cart/types'

export function CartDrawer() {
  const cartDrawerOpen = useUIStore((s) => s.cartDrawerOpen)
  const setCartDrawerOpen = useUIStore((s) => s.setCartDrawerOpen)

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  // Granular selectors — never subscribe to entire store
  const items = useCartStore((s) => s.items)
  const totalItems = useCartStore((s) => s.totalItems())
  const totalPrice = useCartStore((s) => s.totalPrice())
  const removeItem = useCartStore((s) => s.removeItem)
  const updateQuantity = useCartStore((s) => s.updateQuantity)

  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const triggerRef = useRef<HTMLElement | null>(null)

  // Focus management — move focus to close button on open
  useEffect(() => {
    if (cartDrawerOpen) {
      // Save the element that triggered the open so we can return focus on close
      triggerRef.current = document.activeElement as HTMLElement
      // Small delay to let CSS transition start
      setTimeout(() => {
        closeButtonRef.current?.focus()
      }, 50)
    } else {
      // Return focus to the trigger element (CartIcon in Navbar)
      triggerRef.current?.focus()
    }
  }, [cartDrawerOpen])

  // Escape key closes drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && cartDrawerOpen) {
        setCartDrawerOpen(false)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [cartDrawerOpen, setCartDrawerOpen])

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (cartDrawerOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [cartDrawerOpen])

  return (
    <>
      {/* Backdrop overlay — click to close */}
      {cartDrawerOpen && (
        <div
          aria-hidden="true"
          onClick={() => setCartDrawerOpen(false)}
          className="fixed inset-0 bg-foreground/40 backdrop-blur-sm z-40 transition-opacity"
        />
      )}

      {/* Drawer panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Carrito de compras"
        aria-hidden={!cartDrawerOpen}
        className={[
          'fixed inset-y-0 right-0 z-50',
          'w-full sm:w-[420px]',
          'bg-background border-l border-border shadow-2xl',
          'flex flex-col',
          'transition-transform duration-300 ease-in-out',
          cartDrawerOpen ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
      >
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-4 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-foreground" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-foreground">Carrito</h2>
            <span
              aria-live="polite"
              aria-atomic="true"
              className="text-sm text-muted-foreground"
            >
              ({totalItems} {totalItems !== 1 ? 'ítems' : 'ítem'})
            </span>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            onClick={() => setCartDrawerOpen(false)}
            aria-label="Cerrar carrito"
            className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </header>

        {/* Scrollable item list */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {items.length === 0 ? (
            <EmptyCart />
          ) : (
            items.map((item) => (
              <CartItemRow
                key={item.productId}
                item={item}
                onQuantityChange={updateQuantity}
                onRemove={removeItem}
              />
            ))
          )}
        </div>

        {/* Fixed footer with totals + CTAs */}
        {items.length > 0 && (
          <footer className="shrink-0 border-t border-border px-4 py-4 space-y-3 bg-card">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total</span>
              <span className="text-xl font-bold text-foreground">
                {formatCurrency(totalPrice)}
              </span>
            </div>

            <div className="space-y-2">
              {/* View full cart */}
              <Link
                to="/cart"
                onClick={() => setCartDrawerOpen(false)}
                className="block w-full py-2.5 px-4 rounded-md border border-border text-foreground font-medium text-sm text-center hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Ver carrito completo
              </Link>

              {/* Checkout CTA — redirect to login if not authenticated */}
              <Link
                to={isAuthenticated ? '/checkout' : '/login'}
                state={isAuthenticated ? undefined : { from: { pathname: '/checkout' } }}
                onClick={() => setCartDrawerOpen(false)}
                className="block w-full py-2.5 px-4 rounded-md bg-primary text-primary-foreground font-semibold text-sm text-center hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Proceder al pago
              </Link>
            </div>
          </footer>
        )}
      </div>
    </>
  )
}
