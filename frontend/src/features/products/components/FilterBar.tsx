/**
 * FilterBar Component
 *
 * Main filter sidebar with mobile-responsive overlay behaviour.
 *
 * Desktop (md+):
 *   Renders as a sticky sidebar inside the grid column provided by Catalog.tsx.
 *
 * Mobile (<md):
 *   - Renders only a hamburger button (inline, full-width row).
 *   - When open, the filter panel slides in as a fixed overlay (z-50) over the
 *     page — it does NOT occupy grid space, so products are always full-width.
 *   - Backdrop (z-40) closes the panel on outside click.
 *
 * Layout responsibility split:
 *   - Catalog.tsx hides this component's wrapper div on desktop/mobile via
 *     `hidden md:block` / `md:hidden` wrapping divs.
 *   - FilterBar manages only its internal open/close state.
 *
 * Tokens: only semantic @theme tokens (no raw hex/rgb/Tailwind color scales).
 *
 * @component
 */

import { useState } from 'react'
import { Filter, X } from 'lucide-react'
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
 * @param excludeAllergens - Selected allergen IDs to exclude
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

  const activeCount =
    categoryIds.length + excludeAllergens.length + (search.trim() ? 1 : 0)

  const handleClearAll = () => {
    onSearchChange('')
    onCategoryChange([])
    onAllergenChange([])
  }

  // Shared filter panel content — used in both desktop sidebar and mobile overlay
  const filterPanelContent = (
    <div className="divide-y divide-border">
      {/* Search */}
      <div className="py-3">
        <SearchInput
          value={search}
          onChange={onSearchChange}
          placeholder="Search products..."
        />
      </div>

      {/* Categories */}
      <div className="py-3">
        <CategoryFilter
          selectedIds={categoryIds}
          onChange={onCategoryChange}
        />
      </div>

      {/* Allergens — only when current page has products with allergen data */}
      {products && products.length > 0 ? (
        <div className="py-3">
          <AllergenFilter
            allergens={allergens}
            selectedIds={excludeAllergens}
            onChange={onAllergenChange}
          />
        </div>
      ) : null}

      {/* Clear All Button */}
      {activeCount > 0 ? (
        <div className="py-3">
          <button
            onClick={handleClearAll}
            className="w-full px-4 py-2 border border-border text-foreground rounded-lg hover:bg-muted/50 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
            aria-label="Clear all filters"
          >
            Clear All Filters
          </button>
        </div>
      ) : null}
    </div>
  )

  return (
    <>
      {/* ── Mobile: Filter trigger button (full-width row, no grid impact) ── */}
      <div className="md:hidden mb-4">
        <button
          onClick={() => setIsOpen(true)}
          className="inline-flex items-center gap-2 px-3 py-2 bg-secondary text-secondary-foreground border border-border rounded-lg hover:bg-muted/50 transition-colors text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
          aria-label="Open filters"
          aria-expanded={isOpen}
          aria-controls="mobile-filter-panel"
        >
          <Filter size={16} aria-hidden="true" />
          Filtros
          {activeCount > 0 ? (
            <span className="ml-1 inline-flex items-center justify-center h-5 min-w-5 px-1 text-xs font-semibold bg-primary text-primary-foreground rounded-full">
              {activeCount}
            </span>
          ) : null}
        </button>
      </div>

      {/* ── Mobile: Fixed overlay panel (z-50, no layout flow) ── */}
      {isOpen ? (
        <>
          {/* Backdrop — closes panel on outside click (z-40, below panel) */}
          <div
            className="md:hidden fixed inset-0 bg-foreground/25 z-40"
            onClick={() => setIsOpen(false)}
            role="presentation"
            aria-hidden="true"
          />

          {/* Slide-in panel (z-50) */}
          <aside
            id="mobile-filter-panel"
            role="complementary"
            aria-label="Product filters"
            className="md:hidden fixed top-0 left-0 h-full w-72 bg-card z-50 overflow-y-auto shadow-lg p-4"
          >
            {/* Panel header with close button */}
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
              <h2 className="text-base font-semibold text-foreground">Filters</h2>
              <button
                onClick={() => setIsOpen(false)}
                aria-label="Close filters"
                className="text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 rounded-md p-1"
              >
                <X size={20} aria-hidden="true" />
              </button>
            </div>

            {filterPanelContent}
          </aside>
        </>
      ) : null}

      {/* ── Desktop: Static sidebar card ── */}
      <aside
        role="complementary"
        aria-label="Product filters"
        className="hidden md:block bg-card rounded-xl border border-border shadow-sm p-5"
      >
        {filterPanelContent}
      </aside>
    </>
  )
}

export type { FilterBarProps }
