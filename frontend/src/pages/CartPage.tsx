/**
 * CartPage — full-page shopping cart view.
 *
 * FSD layer: pages/ (consumes features/cart and widgets)
 *
 * Layout:
 *   - Desktop (lg+): two-column — items list left (col-span-2), OrderSummary sticky right (col-span-1)
 *   - Mobile: single column — items list, then OrderSummary below (sticky bottom-0 on mobile)
 *
 * State: ALL via useCartStore (zero useState for cart logic).
 * Empty state: EmptyCart component when items.length === 0.
 *
 * Accessibility:
 *   - <main> with aria-label="Carrito de compras"
 *   - <h1> heading with item count
 *   - "Vaciar carrito" only visible when cart has items (text-destructive)
 *
 * Performance:
 *   - Lazy-loaded from Router.tsx (bundle-dynamic-imports)
 *   - CartItemRow extracted component — no inline components (rerender-no-inline-components)
 */

import { useCartStore } from '@/store'
import { CartItemRow, OrderSummary, EmptyCart } from '@/features/cart/components'

export default function CartPage() {
  // Granular selectors
  const items = useCartStore((s) => s.items)
  const totalItems = useCartStore((s) => s.totalItems())
  const removeItem = useCartStore((s) => s.removeItem)
  const updateQuantity = useCartStore((s) => s.updateQuantity)
  const clearCart = useCartStore((s) => s.clearCart)

  const isEmpty = items.length === 0

  return (
    <main
      aria-label="Carrito de compras"
      className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
    >
      {/* Page header with separator */}
      <div className="flex items-center justify-between border-b border-border mb-6 pb-4">
        <h1 className="text-2xl font-bold text-foreground">
          Mi Carrito
          {!isEmpty && (
            <span className="ml-2 text-base font-normal text-muted-foreground">
              ({totalItems} {totalItems !== 1 ? 'ítems' : 'ítem'})
            </span>
          )}
        </h1>
        {!isEmpty && (
          <button
            type="button"
            onClick={clearCart}
            className="text-sm text-destructive hover:text-destructive/80 underline underline-offset-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
          >
            Vaciar carrito
          </button>
        )}
      </div>

      {isEmpty ? (
        <EmptyCart />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-8 items-start">
          {/* Items list */}
          <section aria-label="Productos en el carrito">
            <ul className="space-y-3 list-none p-0">
              {items.map((item) => (
                <li key={item.productId}>
                  <CartItemRow
                    item={item}
                    onQuantityChange={updateQuantity}
                    onRemove={removeItem}
                  />
                </li>
              ))}
            </ul>
          </section>

          {/* Order summary panel — sticky on desktop, visible at bottom on mobile */}
          <div className="lg:sticky lg:top-4">
            <OrderSummary />
          </div>
        </div>
      )}
    </main>
  )
}
