/**
 * Hook: useAllergensFilter
 * 
 * Extracts unique allergens from products list
 * Used to populate allergen exclusion checkboxes
 * 
 * Usage:
 * ```tsx
 * const allergens = useAllergensFilter(products)
 * ```
 */

import { useMemo } from 'react'
import type { Product, Ingredient } from '@/features/products/types'

/**
 * Allergen item for filter UI
 */
export interface AllergenItem {
  id: string
  nombre: string
  count: number // Number of products containing this allergen
}

/**
 * useAllergensFilter Hook
 * 
 * Extracts unique allergens from product list
 * Memoized to avoid recalculating on every render
 * 
 * @param products - List of products
 * @returns Array of unique allergens with counts
 */
export function useAllergensFilter(products: Product[] | undefined): AllergenItem[] {
  return useMemo(() => {
    if (!products || products.length === 0) {
      return []
    }

    const allergenMap = new Map<string, { id: string; nombre: string; count: number }>()

    // Iterate through all products and their ingredients
    products.forEach((product) => {
      product.ingredientes.forEach((ingredient: Ingredient) => {
        // Only track ingredients marked as allergens
        if (ingredient.is_alergeno) {
          const existing = allergenMap.get(ingredient.id) || {
            id: ingredient.id,
            nombre: ingredient.nombre,
            count: 0,
          }
          allergenMap.set(ingredient.id, {
            ...existing,
            count: existing.count + 1,
          })
        }
      })
    })

    // Convert map to sorted array
    return Array.from(allergenMap.values()).sort((a, b) =>
      b.count - a.count, // Sort by frequency (most common first)
    )
  }, [products])
}
