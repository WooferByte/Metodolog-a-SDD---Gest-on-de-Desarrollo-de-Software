/**
 * EmptyCart — rendered when the cart has zero items.
 *
 * Accessibility:
 *   - Decorative SVG: aria-hidden="true"
 *   - h2 heading for screen readers
 *   - Link styled as button with clear CTA text
 */

import { Link } from 'react-router-dom'

export function EmptyCart() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-16 text-center">
      {/* Decorative SVG illustration */}
      <svg
        aria-hidden="true"
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-32 h-32 text-muted-foreground opacity-40"
      >
        {/* Cart body */}
        <rect x="20" y="40" width="80" height="50" rx="8" stroke="currentColor" strokeWidth="4" fill="none" />
        {/* Cart handle */}
        <path d="M20 40L10 15" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
        <path d="M10 15H5" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
        {/* Wheels */}
        <circle cx="40" cy="98" r="7" stroke="currentColor" strokeWidth="4" fill="none" />
        <circle cx="80" cy="98" r="7" stroke="currentColor" strokeWidth="4" fill="none" />
        {/* Empty lines */}
        <path d="M35 62h50M35 74h30" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity="0.5" />
      </svg>

      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-foreground">
          Tu carrito está vacío
        </h2>
        <p className="text-muted-foreground max-w-xs">
          Explorá nuestros productos y agregá lo que más te guste
        </p>
      </div>

      <Link
        to="/catalog"
        className="inline-flex items-center justify-center px-6 py-3 rounded-md bg-primary text-primary-foreground font-semibold text-base hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        Ver productos
      </Link>
    </div>
  )
}
