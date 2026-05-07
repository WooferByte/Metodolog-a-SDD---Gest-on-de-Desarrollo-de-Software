/**
 * AppliedFilters Component
 * 
 * Displays currently active filters as removable tags
 * - Shows category, search, and allergen filters
 * - Each tag has an X button to remove
 * - "Clear All" button to reset all filters
 * 
 * @component
 */

import { X } from 'lucide-react'
import { useCategoriesHierarchy } from '@/features/products/hooks'

interface AppliedFiltersProps {
  search: string
  categoryIds: string[]
  excludeAllergens: string[]
  allergens: Array<{ id: string; nombre: string }>
  onRemoveCategory: (id: string) => void
  onRemoveAllergen: (id: string) => void
  onClearSearch: () => void
  onClearAll: () => void
}

/**
 * AppliedFilters Component
 * 
 * @param search - Current search term
 * @param categoryIds - Selected category IDs
 * @param excludeAllergens - Selected allergen IDs to exclude
 * @param allergens - List of all allergens
 * @param onRemoveCategory - Callback to remove category filter
 * @param onRemoveAllergen - Callback to remove allergen filter
 * @param onClearSearch - Callback to clear search
 * @param onClearAll - Callback to clear all filters
 */
export function AppliedFilters({
  search,
  categoryIds,
  excludeAllergens,
  allergens,
  onRemoveCategory,
  onRemoveAllergen,
  onClearSearch,
  onClearAll,
}: AppliedFiltersProps) {
  const { data: categories = [] } = useCategoriesHierarchy()

  // Check if any filters are active
  const hasActiveFilters = search || categoryIds.length > 0 || excludeAllergens.length > 0

  if (!hasActiveFilters) {
    return null
  }

  // Get category names from IDs
  const getCategoryName = (id: string): string => {
    const cat = categories.find((c: any) => c.id === id)
    return cat?.nombre || id
  }

  // Get allergen names from IDs
  const getAllergenName = (id: string): string => {
    return allergens.find((a) => a.id === id)?.nombre || id
  }

  return (
    <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-semibold text-gray-700">Applied Filters:</p>
        <button
          onClick={onClearAll}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
          aria-label="Clear all filters"
        >
          Clear All
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {/* Search Filter */}
        {search && (
          <div
            className="inline-flex items-center gap-1 px-3 py-1 bg-white border border-blue-300 rounded-full text-sm"
            role="status"
            aria-label={`Search filter: ${search}`}
          >
            <span>Search: {search}</span>
            <button
              onClick={onClearSearch}
              className="ml-1 text-gray-500 hover:text-gray-700 transition-colors"
              aria-label={`Remove search filter: ${search}`}
            >
              <X size={14} />
            </button>
          </div>
        )}

        {/* Category Filters */}
        {categoryIds.map((id) => (
          <div
            key={`cat-${id}`}
            className="inline-flex items-center gap-1 px-3 py-1 bg-white border border-blue-300 rounded-full text-sm"
            role="status"
          >
            <span>Category: {getCategoryName(id)}</span>
            <button
              onClick={() => onRemoveCategory(id)}
              className="ml-1 text-gray-500 hover:text-gray-700 transition-colors"
              aria-label={`Remove category filter: ${getCategoryName(id)}`}
            >
              <X size={14} />
            </button>
          </div>
        ))}

        {/* Allergen Filters */}
        {excludeAllergens.map((id) => (
          <div
            key={`allergen-${id}`}
            className="inline-flex items-center gap-1 px-3 py-1 bg-red-50 border border-red-300 rounded-full text-sm"
            role="status"
          >
            <span>Excluding: {getAllergenName(id)}</span>
            <button
              onClick={() => onRemoveAllergen(id)}
              className="ml-1 text-red-600 hover:text-red-800 transition-colors"
              aria-label={`Remove allergen filter: ${getAllergenName(id)}`}
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export type { AppliedFiltersProps }
