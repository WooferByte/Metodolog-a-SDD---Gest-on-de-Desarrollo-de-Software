/**
 * CartItemRow — renders a single cart item.
 *
 * Layout mobile: image left (80×80), content right in column.
 * Layout desktop (sm+): image 96×96, wider layout.
 *
 * Accessibility (WCAG 2.1 AA):
 *   - article with aria-label="Producto: {name}"
 *   - remove button: aria-label="Eliminar {name} del carrito"
 *   - image alt text or role="presentation" on fallback
 *
 * Animation: entry slide-in-down via CSS @keyframes (defined in index.css).
 *   Uses @starting-style via inline style + animate utility.
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
      className="flex gap-4 p-4 bg-card border border-border rounded-lg hover:border-ring transition-colors animate-[slide-in-down_0.2s_ease-out]"
    >
      {/* Product image — 80×80 mobile, 96×96 desktop (sm+) */}
      <div className="shrink-0">
        {item.image ? (
          <img
            src={item.image}
            alt={item.name}
            loading="lazy"
            width={96}
            height={96}
            className="w-20 h-20 sm:w-24 sm:h-24 object-cover rounded-md bg-muted"
            onError={(e) => {
              const img = e.currentTarget
              img.style.display = 'none'
              if (img.nextElementSibling) {
                (img.nextElementSibling as HTMLElement).style.display = 'flex'
              }
            }}
          />
        ) : null}
        {/* Fallback — elegant gradient with initial letter, not plain grey */}
        <div
          role="img"
          aria-label={`Imagen de ${item.name}`}
          className="w-20 h-20 sm:w-24 sm:h-24 rounded-md bg-gradient-to-br from-brand/20 to-brand/40 flex items-center justify-center text-2xl font-bold text-brand-foreground select-none"
          style={{ display: item.image ? 'none' : 'flex' }}
        >
          {item.name.charAt(0).toUpperCase()}
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

        {/* Ingredientes excluidos — visual badge pills (task 2.2) */}
        {item.ingredientes_excluidos && item.ingredientes_excluidos.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5" aria-label="Personalizaciones">
            {item.ingredientes_excluidos.map((ingredienteId) => (
              <span
                key={ingredienteId}
                className="bg-muted border border-border text-xs rounded-full px-2 py-0.5 text-muted-foreground"
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

        {/* Subtotal — own line, right-aligned (task 2.4) */}
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
