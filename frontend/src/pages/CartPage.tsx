/**
 * CartPage — full-page shopping cart view.
 *
 * FSD layer: pages/ (consumes features/cart and widgets)
 *
 * Layout:
 *   - Desktop (lg+): two-column — items list left, OrderSummary sticky right
 *   - Mobile: single column — items list, then OrderSummary below
 *
 * State: ALL via useCartStore (zero useState for cart logic).
 * Empty state: EmptyCart component when items.length === 0.
 *
 * Accessibility:
 *   - <main> with aria-label="Carrito de compras"
 *   - <h1> heading
 *   - "Vaciar carrito" only visible when cart has items
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
  const removeItem = useCartStore((s) => s.removeItem)
  const updateQuantity = useCartStore((s) => s.updateQuantity)
  const clearCart = useCartStore((s) => s.clearCart)

  const isEmpty = items.length === 0

  return (
    <main
      aria-label="Carrito de compras"
      className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
    >
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-foreground">Mi carrito</h1>
        {!isEmpty && (
          <button
            type="button"
            onClick={clearCart}
            className="text-sm text-muted-foreground hover:text-destructive underline underline-offset-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
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

          {/* Order summary panel */}
          <div>
            <OrderSummary />
          </div>
        </div>
      )}
    </main>
  )
}
