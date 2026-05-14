/**
 * EmptyCart — rendered when the cart has zero items.
 *
 * Accessibility:
 *   - Decorative SVG: aria-hidden="true" (food store themed — plate + utensils)
 *   - h2 heading for screen readers
 *   - Link styled as primary button with CTA text + lucide icon
 *   - Focus ring visible for keyboard navigation
 */

import { Link } from 'react-router-dom'
import { UtensilsCrossed } from 'lucide-react'

export function EmptyCart() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-16 text-center">
      {/* Decorative food store SVG — plate with fork and knife, empty tray */}
      <svg
        aria-hidden="true"
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-16 h-16 text-muted-foreground opacity-50"
      >
        {/* Plate */}
        <circle cx="60" cy="62" r="36" stroke="currentColor" strokeWidth="4" fill="none" />
        {/* Inner plate ring */}
        <circle cx="60" cy="62" r="26" stroke="currentColor" strokeWidth="2.5" fill="none" opacity="0.4" />
        {/* Fork — left of plate */}
        <path d="M28 24 L28 42 M24 24 L24 36 M32 24 L32 36 M28 42 L28 56" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        {/* Knife — right of plate */}
        <path d="M92 24 C92 24 96 30 96 36 C96 40 92 42 92 42 L92 56" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        {/* Small dot — empty plate hint */}
        <circle cx="60" cy="62" r="3" fill="currentColor" opacity="0.3" />
      </svg>

      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-foreground">
          Tu carrito está vacío
        </h2>
        <p className="text-muted-foreground max-w-xs">
          ¿Qué se te antoja hoy? — ¡explorá nuestro menú!
        </p>
      </div>

      <Link
        to="/catalog"
        className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-md bg-primary text-primary-foreground font-semibold text-base hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        <UtensilsCrossed className="h-4 w-4" aria-hidden="true" />
        Ver el menú
      </Link>
    </div>
  )
}
