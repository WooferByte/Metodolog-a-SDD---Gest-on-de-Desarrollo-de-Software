/**
 * PaymentMethodSelector — WCAG AA compliant radio group for payment method selection.
 *
 * Implements WAI-ARIA radiogroup pattern:
 *   - Container: role="radiogroup" aria-label="Método de pago"
 *   - Each option: role="radio" aria-checked aria-disabled
 *   - Keyboard: Arrow keys move between enabled options, Space/Enter selects
 *
 * Uses Tailwind v4 semantic tokens only (no raw colors).
 * Reads options from paymentMethods.ts constants.
 */

import { useRef, type KeyboardEvent } from 'react'
import { usePaymentStore } from '@/store/paymentStore'
import { PAYMENT_METHODS } from '../constants/paymentMethods'
import type { PaymentMethodOption } from '../types/payment.types'

interface PaymentMethodSelectorProps {
  /** Optional className override for the container */
  className?: string
}

export function PaymentMethodSelector({ className }: PaymentMethodSelectorProps) {
  const method = usePaymentStore((state) => state.method)
  const setMethod = usePaymentStore((state) => state.setMethod)

  const enabledMethods = PAYMENT_METHODS.filter((m) => m.enabled)
  const containerRef = useRef<HTMLDivElement>(null)

  function handleSelect(option: PaymentMethodOption) {
    if (!option.enabled) return
    // Only set if it's a valid PaymentMethod (mercadopago | cash)
    if (option.id === 'mercadopago' || option.id === 'cash') {
      setMethod(option.id)
    }
  }

  /**
   * WCAG radiogroup keyboard navigation pattern:
   *   - ArrowDown / ArrowRight → next enabled option
   *   - ArrowUp / ArrowLeft → previous enabled option
   *   - Space / Enter → select focused option
   *   - Home → first enabled option
   *   - End → last enabled option
   */
  function handleKeyDown(e: KeyboardEvent<HTMLDivElement>, currentIndex: number) {
    const total = PAYMENT_METHODS.length
    let nextIndex = currentIndex

    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
      e.preventDefault()
      // Find next enabled option
      let i = (currentIndex + 1) % total
      while (i !== currentIndex) {
        if (PAYMENT_METHODS[i].enabled) { nextIndex = i; break }
        i = (i + 1) % total
      }
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
      e.preventDefault()
      // Find previous enabled option
      let i = (currentIndex - 1 + total) % total
      while (i !== currentIndex) {
        if (PAYMENT_METHODS[i].enabled) { nextIndex = i; break }
        i = (i - 1 + total) % total
      }
    } else if (e.key === 'Home') {
      e.preventDefault()
      const first = PAYMENT_METHODS.findIndex((m) => m.enabled)
      if (first !== -1) nextIndex = first
    } else if (e.key === 'End') {
      e.preventDefault()
      const last = [...PAYMENT_METHODS].reverse().findIndex((m) => m.enabled)
      if (last !== -1) nextIndex = PAYMENT_METHODS.length - 1 - last
    } else if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault()
      handleSelect(PAYMENT_METHODS[currentIndex])
      return
    } else {
      return
    }

    // Move focus to the next option
    if (nextIndex !== currentIndex) {
      const radios = containerRef.current?.querySelectorAll('[role="radio"]')
      if (radios && radios[nextIndex]) {
        (radios[nextIndex] as HTMLElement).focus()
      }
    }
  }

  return (
    <div
      ref={containerRef}
      role="radiogroup"
      aria-label="Método de pago"
      className={className}
    >
      <p className="text-sm font-medium text-foreground mb-3">
        Seleccioná un método de pago
      </p>

      <div className="flex flex-col gap-3">
        {PAYMENT_METHODS.map((option, index) => {
          const isSelected = method === option.id
          const isDisabled = !option.enabled

          return (
            <div
              key={option.id}
              role="radio"
              aria-checked={isSelected}
              aria-disabled={isDisabled}
              tabIndex={isDisabled ? -1 : isSelected ? 0 : (enabledMethods.indexOf(option) === 0 && method === null ? 0 : -1)}
              onClick={() => handleSelect(option)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              data-testid={`payment-method-${option.id}`}
              className={[
                'flex items-start gap-4 rounded-lg border p-4 transition-colors',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                isDisabled
                  ? 'cursor-not-allowed border-border bg-muted opacity-50'
                  : 'cursor-pointer',
                !isDisabled && isSelected
                  ? 'border-primary bg-primary/5'
                  : !isDisabled
                  ? 'border-border bg-card hover:border-primary/50 hover:bg-accent/30'
                  : '',
              ].join(' ')}
            >
              {/* Radio indicator */}
              <div
                className={[
                  'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors',
                  isSelected && !isDisabled
                    ? 'border-primary'
                    : 'border-border',
                ].join(' ')}
                aria-hidden="true"
              >
                {isSelected && !isDisabled && (
                  <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                )}
              </div>

              {/* Icon + label + description */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span aria-hidden="true" className="text-xl">{option.icon}</span>
                  <span
                    className={[
                      'font-medium text-sm',
                      isDisabled ? 'text-muted-foreground' : 'text-foreground',
                    ].join(' ')}
                  >
                    {option.label}
                  </span>
                  {isDisabled && (
                    <span className="ml-auto text-xs text-muted-foreground">
                      Próximamente
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                  {option.description}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
