/**
 * ProductCard Component
 * 
 * Displays a product in thumbnail form with:
 * - Product image with lazy loading
 * - Product name and price
 * - Availability badge (In Stock / Out of Stock)
 * - "View Details" and "Add to Cart" buttons
 * 
 * Accessibility:
 * - Alt text on images for screen readers
 * - Semantic HTML buttons
 * - Keyboard navigable
 * 
 * @component
 * @example
 * ```tsx
 * <ProductCard
 *   product={product}
 *   onViewDetails={(product) => setSelectedProduct(product)}
 *   onAddToCart={(product) => handleAddToCart(product)}
 * />
 * ```
 */

import { ShoppingCart, Eye } from 'lucide-react'
import type { ProductCardProps } from '@/features/products/types'

/**
 * ProductCard Component
 * 
 * @param product - Product data to display
 * @param onViewDetails - Callback when "View Details" is clicked
 * @param onAddToCart - Callback when "Add to Cart" is clicked
 */
export function ProductCard({
  product,
  onViewDetails,
  onAddToCart,
}: ProductCardProps) {
  const isAvailable = product.disponible && product.stock_cantidad > 0
  const priceFormatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(product.precio)

  /**
   * Fallback image for broken/missing images
   */
  const handleImageError = (event: React.SyntheticEvent<HTMLImageElement>) => {
    const img = event.currentTarget
    img.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22Arial%22 font-size=%2216%22 fill=%22%23999%22%3ENo Image%3C/text%3E%3C/svg%3E'
  }

  return (
    <article
      className="bg-card rounded-lg shadow-md hover:shadow-xl transition-shadow overflow-hidden flex flex-col"
      role="article"
      aria-label={`Product: ${product.nombre}`}
    >
      {/* Image Container */}
      <div className="relative overflow-hidden bg-muted h-48">
        <img
          src={product.imagen_url}
          alt={product.nombre}
          className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
          loading="lazy"
          onError={handleImageError}
        />
        
        {/* Availability Badge */}
        <div className="absolute top-2 right-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              isAvailable
                ? 'bg-success/10 text-success'
                : 'bg-destructive/10 text-destructive'
            }`}
            role="status"
          >
            {isAvailable ? 'In Stock' : 'Out of Stock'}
          </span>
        </div>

        {/* Allergen Indicator */}
        {product.ingredientes.some((ing) => ing.is_alergeno) && (
          <div
            className="absolute bottom-2 left-2 bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-semibold"
            role="img"
            aria-label="Contains allergens"
            title="This product contains allergens"
          >
            ⚠️ Allergens
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4 flex-1 flex flex-col">
        {/* Name */}
        <h3 className="font-semibold text-lg text-foreground mb-2 line-clamp-2">
          {product.nombre}
        </h3>

        {/* Description */}
        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
          {product.descripcion}
        </p>

        {/* Price */}
        <p className="text-xl font-bold text-primary mb-4">
          {priceFormatted}
        </p>

        {/* Actions */}
        <div className="flex gap-2 mt-auto">
          {/* View Details Button */}
          <button
            onClick={() => onViewDetails(product)}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground rounded-lg font-medium transition-colors"
            aria-label={`View details for ${product.nombre}`}
          >
            <Eye size={16} />
            <span className="hidden sm:inline">Details</span>
          </button>

          {/* Add to Cart Button */}
          <button
            onClick={() => onAddToCart(product)}
            disabled={!isAvailable}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-success hover:bg-success/90 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
            aria-label={`Add ${product.nombre} to cart${!isAvailable ? ' (unavailable)' : ''}`}
          >
            <ShoppingCart size={16} />
            <span className="hidden sm:inline">Add</span>
          </button>
        </div>
      </div>
    </article>
  )
}

export type { ProductCardProps }
