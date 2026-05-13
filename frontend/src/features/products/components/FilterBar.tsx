/**
 * FilterBar Component
 * 
 * Main filter sidebar:
 * - Search input
 * - Category filter dropdown
 * - Allergen exclusion checkboxes
 * - Collapsible on mobile (hamburger)
 * 
 * @component
 */

import { useState } from 'react'
import { Menu, X } from 'lucide-react'
import { SearchInput } from './SearchInput'
import { CategoryFilter } from './CategoryFilter'
import { AllergenFilter } from './AllergenFilter'
import { useAllergensFilter } from '@/features/products/hooks'
import type { Product } from '@/features/products/types'

interface FilterBarProps {
  search: string
  categoryIds: string[]
  excludeAllergens: string[]
  products: Product[] | undefined
  onSearchChange: (value: string) => void
  onCategoryChange: (ids: string[]) => void
  onAllergenChange: (ids: string[]) => void
}

/**
 * FilterBar Component
 * 
 * @param search - Current search value
 * @param categoryIds - Selected category IDs
 * @param excludeAllergens - Selected allergen IDs
 * @param products - Products for allergen extraction
 * @param onSearchChange - Callback when search changes
 * @param onCategoryChange - Callback when categories change
 * @param onAllergenChange - Callback when allergens change
 */
export function FilterBar({
  search,
  categoryIds,
  excludeAllergens,
  products,
  onSearchChange,
  onCategoryChange,
  onAllergenChange,
}: FilterBarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const allergens = useAllergensFilter(products)

  const handleClearAll = () => {
    onSearchChange('')
    onCategoryChange([])
    onAllergenChange([])
  }

  return (
    <>
      {/* Mobile: Hamburger Toggle */}
      <div className="md:hidden mb-4">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          aria-label={isOpen ? 'Close filters' : 'Open filters'}
          aria-expanded={isOpen}
        >
          {isOpen ? <X size={20} /> : <Menu size={20} />}
          Filters
        </button>
      </div>

      {/* Filter Sidebar */}
      <aside
        className={`${
          isOpen ? 'block' : 'hidden'
        } md:block md:w-64 bg-card rounded-lg shadow-md p-4 space-y-6 mb-4 md:mb-0`}
        role="complementary"
        aria-label="Product filters"
      >
        {/* Search */}
        <div>
          <SearchInput
            value={search}
            onChange={onSearchChange}
            placeholder="Search products..."
          />
        </div>

        {/* Categories */}
        <CategoryFilter
          selectedIds={categoryIds}
          onChange={onCategoryChange}
        />

        {/* Allergens */}
        {products && products.length > 0 && (
          <AllergenFilter
            allergens={allergens}
            selectedIds={excludeAllergens}
            onChange={onAllergenChange}
          />
        )}

        {/* Clear All Button */}
        {(search || categoryIds.length > 0 || excludeAllergens.length > 0) && (
          <button
            onClick={handleClearAll}
            className="w-full px-4 py-2 border-2 border-border text-foreground rounded-lg hover:bg-muted/50 font-medium transition-colors"
            aria-label="Clear all filters"
          >
            Clear All Filters
          </button>
        )}
      </aside>

      {/* Mobile: Close filter panel when opening ProductDetail */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black bg-opacity-25 z-40"
          onClick={() => setIsOpen(false)}
          role="presentation"
        />
      )}
    </>
  )
}

export type { FilterBarProps }
