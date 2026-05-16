/**
 * ProductDetail Modal Component
 * 
 * Full-screen modal for viewing complete product details:
 * - Product image
 * - Name, description, price
 * - Categories as tags
 * - Ingredients list with allergen indicators
 * - Quantity selector
 * - Add to Cart button
 * 
 * Features:
 * - Closes on Escape key
 * - Closes on backdrop click
 * - Focus trap (Tab cycles within modal)
 * - Restores focus when closed
 * - Responsive (full-width on mobile, centered on desktop)
 * 
 * @component
 */

import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, AlertTriangle, Plus, Minus } from 'lucide-react'
import { apiClient } from '@/shared/api/axios'
import type { Product } from '@/features/products/types'
import { MIN_QUANTITY, MAX_QUANTITY } from '@/features/products/constants'

interface ProductDetailProps {
  product: Product | null
  isOpen: boolean
  onClose: () => void
  onAddToCart: (product: Product, quantity: number) => void
}

export function ProductDetail({
  product,
  isOpen,
  onClose,
  onAddToCart,
}: ProductDetailProps) {
  const [quantity, setQuantity] = useState(1)
  const modalRef = useRef<HTMLDivElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  // Fetch full product data (with ingredientes) when modal opens
  const { data: fullProduct } = useQuery<Product>({
    queryKey: ['product-detail', product?.id],
    queryFn: async () => {
      const res = await apiClient.get<Product>(`/api/v1/productos/${product!.id}`)
      return res.data
    },
    enabled: isOpen && product != null,
    staleTime: 1000 * 60 * 5,
  })

  // Merge: use fresh data when available, fall back to catalog data
  const displayProduct = fullProduct ?? product

  // Reset quantity when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuantity(1)
      closeButtonRef.current?.focus()
    }
  }, [isOpen])

  // Handle Escape key to close modal
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  // Implement focus trap
  useEffect(() => {
    if (!isOpen || !modalRef.current) return

    const focusableElements = modalRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    )

    const firstElement = focusableElements[0] as HTMLElement
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      if (event.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          event.preventDefault()
          lastElement?.focus()
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          event.preventDefault()
          firstElement?.focus()
        }
      }
    }

    document.addEventListener('keydown', handleTabKey)
    return () => document.removeEventListener('keydown', handleTabKey)
  }, [isOpen])

  if (!isOpen || !displayProduct) return null

  const priceNum = parseFloat(String(displayProduct.precio_base))
  const priceFormatted = isFinite(priceNum)
    ? new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(priceNum)
    : '—'

  const hasAllergens = displayProduct.ingredientes.some((ing) => ing.es_alergeno)

  const handleImageError = (event: React.SyntheticEvent<HTMLImageElement>) => {
    event.currentTarget.src =
      'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22400%22 height=%22300%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22Arial%22 font-size=%2220%22 fill=%22%23999%22%3ENo Image Available%3C/text%3E%3C/svg%3E'
  }

  const handleAddToCart = () => {
    onAddToCart(displayProduct, quantity)
    onClose()
  }

  const incrementQuantity = () => {
    setQuantity((prev) => Math.min(prev + 1, MAX_QUANTITY))
  }

  const decrementQuantity = () => {
    setQuantity((prev) => Math.max(prev - 1, MIN_QUANTITY))
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
        role="presentation"
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        ref={modalRef}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="bg-card rounded-lg shadow-xl max-w-2xl w-full my-8">
          {/* Close Button */}
          <button
            ref={closeButtonRef}
            onClick={onClose}
            className="absolute top-4 right-4 p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors z-10"
            aria-label="Cerrar"
            title="Press Escape to close"
          >
            <X size={24} />
          </button>

          {/* Content */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
            {/* Image */}
            <div className="flex items-center justify-center bg-muted rounded-lg overflow-hidden">
              <img
                src={displayProduct.imagen_url}
                alt={displayProduct.nombre}
                className="w-full h-full object-cover max-h-96"
                onError={handleImageError}
              />
            </div>

            {/* Details */}
            <div className="flex flex-col">
              {/* Title */}
              <h2 id="modal-title" className="text-3xl font-bold text-foreground mb-2">
                {displayProduct.nombre}
              </h2>

              {/* Price */}
              <p className="text-2xl font-bold text-primary mb-4">
                {priceFormatted}
              </p>

              {/* Description */}
              <p className="text-foreground mb-4 flex-1">
                {displayProduct.descripcion}
              </p>

              {/* Categories */}
              {displayProduct.categorias.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-semibold text-foreground mb-2">Categories:</p>
                  <div className="flex flex-wrap gap-2">
                    {displayProduct.categorias.map((cat) => (
                      <span
                        key={cat.id}
                        className="px-3 py-1 bg-accent text-accent-foreground rounded-full text-sm"
                      >
                        {cat.nombre}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Allergen Warning */}
              {hasAllergens && (
                <div className="mb-4 p-3 bg-warning/10 border border-warning/30 rounded-lg flex gap-2">
                  <AlertTriangle size={20} className="text-warning flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-warning text-sm">Contains Allergens</p>
                    <p className="text-warning/80 text-sm">
                      See ingredients list below for details
                    </p>
                  </div>
                </div>
              )}

              {/* Ingredients */}
              <div className="mb-6">
                <p className="text-sm font-semibold text-foreground mb-2">Ingredients:</p>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {displayProduct.ingredientes.length > 0 ? (
                    displayProduct.ingredientes.map((ingredient) => (
                      <div
                        key={ingredient.id}
                        className={`text-sm p-2 rounded ${
                          ingredient.es_alergeno
                            ? 'bg-destructive/10 text-destructive border border-destructive/20'
                            : 'text-foreground'
                        }`}
                      >
                        {ingredient.es_alergeno && (
                          <span className="font-semibold mr-2">🔴</span>
                        )}
                        {ingredient.nombre}
                      </div>
                    ))
                  ) : (
                    <p className="text-muted-foreground text-sm">No ingredients listed</p>
                  )}
                </div>
              </div>

              {/* Quantity Selector */}
              <div className="mb-4">
                <label htmlFor="quantity" className="text-sm font-semibold text-foreground block mb-2">
                  Quantity:
                </label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={decrementQuantity}
                    disabled={quantity <= MIN_QUANTITY}
                    className="p-2 bg-muted hover:bg-muted/80 disabled:opacity-50 rounded-lg transition-colors"
                    aria-label="Decrease quantity"
                  >
                    <Minus size={20} />
                  </button>
                  <input
                    id="quantity"
                    type="number"
                    min={MIN_QUANTITY}
                    max={MAX_QUANTITY}
                    value={quantity}
                    onChange={(e) => {
                      const val = parseInt(e.currentTarget.value) || MIN_QUANTITY
                      setQuantity(Math.min(Math.max(val, MIN_QUANTITY), MAX_QUANTITY))
                    }}
                    className="w-16 px-2 py-2 border border-border rounded-lg text-center font-semibold"
                  />
                  <button
                    onClick={incrementQuantity}
                    disabled={quantity >= MAX_QUANTITY}
                    className="p-2 bg-muted hover:bg-muted/80 disabled:opacity-50 rounded-lg transition-colors"
                    aria-label="Increase quantity"
                  >
                    <Plus size={20} />
                  </button>
                </div>
              </div>

              {/* Add to Cart Button */}
              <button
                onClick={handleAddToCart}
                className="w-full px-6 py-3 bg-success hover:bg-success/90 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
              >
                <Plus size={20} />
                Add to Cart
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export type { ProductDetailProps }
