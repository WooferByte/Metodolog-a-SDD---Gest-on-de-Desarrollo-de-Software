/**
 * CartItemRow — renders a single cart item.
 *
 * Layout mobile: image left (80×80), content right in column.
 * Layout desktop (sm+): flex-row with image, name+price, stepper+remove.
 *
 * Accessibility (WCAG 2.1 AA):
 *   - article with aria-label="Producto: {name}"
 *   - remove button: aria-label="Eliminar {name} del carrito"
 *   - image alt text or role="presentation" on fallback
 *
 * Styling: Only semantic Tailwind v4 tokens — zero raw colors.
 */

import { Trash2 } from 'lucide-react'
import type { CartItem } from '@/store'
import { formatCurrency } from '@/features/cart/types'
import { QuantityStepper } from './QuantityStepper'

interface CartItemRowProps {
  item: CartItem
  onQuantityChange: (productId: string, qty: number) => void
  onRemove: (productId: string) => void
}

export function CartItemRow({ item, onQuantityChange, onRemove }: CartItemRowProps) {
  const handleQuantityChange = (newQty: number) => {
    if (newQty === 0) {
      onRemove(item.productId)
    } else {
      onQuantityChange(item.productId, newQty)
    }
  }

  return (
    <article
      role="article"
      aria-label={`Producto: ${item.name}`}
      className="flex gap-4 p-4 bg-card border border-border rounded-lg hover:border-ring transition-colors"
    >
      {/* Product image */}
      <div className="shrink-0">
        {item.image ? (
          <img
            src={item.image}
            alt={item.name}
            loading="lazy"
            width={80}
            height={80}
            className="w-20 h-20 object-cover rounded-md bg-muted"
            onError={(e) => {
              const img = e.currentTarget
              img.style.display = 'none'
              if (img.nextElementSibling) {
                (img.nextElementSibling as HTMLElement).style.display = 'flex'
              }
            }}
          />
        ) : null}
        {/* Fallback — always in DOM; hidden when image loads */}
        <div
          role="img"
          aria-label={`Imagen de ${item.name}`}
          className="w-20 h-20 rounded-md bg-muted flex items-center justify-center text-3xl"
          style={{ display: item.image ? 'none' : 'flex' }}
        >
          🍔
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Name + price row */}
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <h3 className="text-base font-semibold text-foreground leading-tight truncate">
            {item.name}
          </h3>
          <p className="text-lg font-bold text-primary shrink-0">
            {formatCurrency(item.price)}
          </p>
        </div>

        {/* Ingredientes excluidos pills */}
        {item.ingredientes_excluidos && item.ingredientes_excluidos.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {item.ingredientes_excluidos.map((ingredienteId) => (
              <span
                key={ingredienteId}
                className="text-xs text-muted-foreground bg-muted rounded px-2 py-0.5"
              >
                Sin: #{ingredienteId}
              </span>
            ))}
          </div>
        )}

        {/* Stepper + remove — separate so they don't crowd at 375px */}
        <div className="flex items-center justify-between mt-3">
          <QuantityStepper
            value={item.quantity}
            onChange={handleQuantityChange}
            productName={item.name}
          />

          <button
            type="button"
            onClick={() => onRemove(item.productId)}
            aria-label={`Eliminar ${item.name} del carrito`}
            title="Eliminar del carrito"
            className="p-2 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Subtotal — own line, right-aligned */}
        <p className="text-xs text-right text-muted-foreground mt-1">
          Subtotal:{' '}
          <span className="font-semibold text-foreground">
            {formatCurrency(item.price * item.quantity)}
          </span>
        </p>
      </div>
    </article>
  )
}
