/**
 * QuantityStepper — accessible +/− quantity input.
 *
 * Accessibility (WCAG 2.1 AA):
 *   - role="group" with aria-label="Cantidad de {productName}"
 *   - Each button has a descriptive aria-label
 *   - Input has aria-label and type="number" with min/max
 *   - At min: decrement shows trash icon + "Eliminar" affordance; calls onChange(0)
 *   - Parent (CartItemRow) decides whether to remove the item at quantity=0
 *
 * Styling: Only semantic tokens — zero raw colors.
 * Touch targets: minimum 40×40px (mobile-first).
 */

import { Minus, Plus, Trash2 } from 'lucide-react'

interface QuantityStepperProps {
  value: number
  min?: number
  max?: number
  onChange: (newValue: number) => void
  productName: string
}

export function QuantityStepper({
  value,
  min = 1,
  max = 99,
  onChange,
  productName,
}: QuantityStepperProps) {
  const isAtMin = value <= min
  const isAtMax = value >= max

  const handleDecrement = () => {
    if (isAtMin) {
      // At minimum — trigger "remove" by passing 0; parent decides action
      onChange(0)
    } else {
      onChange(value - 1)
    }
  }

  const handleIncrement = () => {
    if (!isAtMax) {
      onChange(value + 1)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const parsed = parseInt(e.target.value, 10)
    if (!isNaN(parsed)) {
      if (parsed < min) {
        onChange(0) // below min triggers remove
      } else if (parsed > max) {
        onChange(max)
      } else {
        onChange(parsed)
      }
    }
  }

  return (
    <div
      role="group"
      aria-label={`Cantidad de ${productName}`}
      className="inline-flex items-center rounded-md border border-border bg-secondary"
    >
      {/* Decrement / Remove button */}
      <button
        type="button"
        onClick={handleDecrement}
        aria-label={isAtMin ? `Eliminar ${productName}` : 'Disminuir cantidad'}
        title={isAtMin ? 'Eliminar del carrito' : 'Disminuir cantidad'}
        className="flex items-center justify-center w-10 h-10 rounded-l-md text-secondary-foreground hover:bg-accent hover:text-accent-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isAtMin ? (
          <Trash2 className="h-4 w-4 text-destructive" aria-hidden="true" />
        ) : (
          <Minus className="h-4 w-4" aria-hidden="true" />
        )}
      </button>

      {/* Quantity display */}
      <input
        type="number"
        value={value}
        onChange={handleInputChange}
        min={min}
        max={max}
        aria-label="Cantidad"
        className="w-10 h-10 text-center text-sm font-mono bg-transparent text-secondary-foreground border-x border-border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
      />

      {/* Increment button */}
      <button
        type="button"
        onClick={handleIncrement}
        disabled={isAtMax}
        aria-label="Aumentar cantidad"
        title="Aumentar cantidad"
        className="flex items-center justify-center w-10 h-10 rounded-r-md text-secondary-foreground hover:bg-accent hover:text-accent-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Plus className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  )
}

