/**
 * ProductGrid Component
 * 
 * Displays products in a responsive grid layout with:
 * - Skeleton loaders while data is loading
 * - "No products found" message when empty
 * - Error state with retry button
 * - Responsive columns (1 mobile, 2 tablet, 3-4 desktop)
 * 
 * @component
 */

import { ProductCard } from './ProductCard'
import type { Product } from '@/features/products/types'

interface ProductGridProps {
  products: Product[] | undefined
  isLoading: boolean
  isError: boolean
  error?: Error | null
  onRetry?: () => void
  onViewDetails: (product: Product) => void
  onAddToCart: (product: Product) => void
}

/**
 * Skeleton Loader Component
 */
function SkeletonCard() {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="bg-gray-200 h-48 animate-pulse" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 bg-gray-200 rounded w-2/3 animate-pulse" />
        <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse" />
        <div className="flex gap-2">
          <div className="flex-1 h-10 bg-gray-200 rounded animate-pulse" />
          <div className="flex-1 h-10 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
    </div>
  )
}

/**
 * ProductGrid Component
 * 
 * @param products - Array of products to display
 * @param isLoading - Whether data is currently loading
 * @param isError - Whether an error occurred
 * @param error - Error object if isError is true
 * @param onRetry - Callback to retry loading
 * @param onViewDetails - Callback when product details requested
 * @param onAddToCart - Callback when add to cart clicked
 */
export function ProductGrid({
  products,
  isLoading,
  isError,
  error,
  onRetry,
  onViewDetails,
  onAddToCart,
}: ProductGridProps) {
  // Loading state with skeleton loaders
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array(20)
          .fill(0)
          .map((_, i) => (
            <SkeletonCard key={i} />
          ))}
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div className="py-12 text-center">
        <div className="inline-block p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-semibold mb-2">
            {error?.message || 'Failed to load products'}
          </p>
          <p className="text-red-700 text-sm mb-4">Please try again later</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              aria-label="Retry loading products"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  // Empty state
  if (!products || products.length === 0) {
    return (
      <div className="py-12 text-center">
        <div className="inline-block p-4">
          <p className="text-gray-600 text-lg font-medium mb-2">No products found</p>
          <p className="text-gray-500 text-sm">
            Try adjusting your filters or search term
          </p>
        </div>
      </div>
    )
  }

  // Products grid
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          onViewDetails={onViewDetails}
          onAddToCart={onAddToCart}
        />
      ))}
    </div>
  )
}

export type { ProductGridProps }
