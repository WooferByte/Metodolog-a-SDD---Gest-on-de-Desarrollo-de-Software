/**
 * CategoryFilter Component
 *
 * Multi-select category list with hierarchical structure.
 * Desktop: always-visible list with checkboxes.
 * Mobile: collapsed dropdown with checkboxes.
 *
 * Tokens: only semantic @theme tokens — no raw hex or Tailwind color scales.
 * Accessibility: WCAG AA — each checkbox wrapped in <label> for full click area.
 *
 * @component
 */

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { useCategoriesHierarchy, buildCategoryHierarchy } from '@/features/products/hooks'

interface CategoryFilterProps {
  selectedIds: string[]
  onChange: (ids: string[]) => void
}

/**
 * CategoryFilter Component
 *
 * @param selectedIds - Array of selected category IDs
 * @param onChange - Callback with new selected IDs
 */
export function CategoryFilter({ selectedIds, onChange }: CategoryFilterProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { data: categories = [], isPending } = useCategoriesHierarchy()
  const hierarchy = buildCategoryHierarchy(categories)

  const handleToggle = (categoryId: string) => {
    const newIds = selectedIds.includes(categoryId)
      ? selectedIds.filter((id) => id !== categoryId)
      : [...selectedIds, categoryId]
    onChange(newIds)
  }

  const handleClearAll = () => {
    onChange([])
  }

  if (isPending) {
    return (
      <div className="space-y-2">
        <div className="h-4 bg-muted rounded animate-pulse" />
        <div className="h-8 bg-muted rounded animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {/* Section heading */}
      <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide mb-3">
        Categories
      </h3>

      {/* Desktop: Always-visible list */}
      <div className="hidden md:block space-y-0.5">
        {hierarchy.parents.map((parent) => (
          <div key={parent.id}>
            {/* Parent Category */}
            <label className="flex items-center gap-2 hover:bg-muted/50 rounded-md px-2 py-1.5 -mx-2 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={selectedIds.includes(parent.id)}
                onChange={() => handleToggle(parent.id)}
                className="w-4 h-4 accent-primary rounded border-border cursor-pointer focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
                aria-label={`Filter by category: ${parent.nombre}`}
              />
              <span className="text-sm font-medium text-foreground leading-none">
                {parent.nombre}
              </span>
            </label>

            {/* Child Categories */}
            {hierarchy.getChildren(parent.id).map((child) => (
              <label
                key={child.id}
                className="flex items-center gap-2 hover:bg-muted/50 rounded-md px-2 py-1.5 -mx-2 pl-6 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedIds.includes(child.id)}
                  onChange={() => handleToggle(child.id)}
                  className="w-4 h-4 accent-primary rounded border-border cursor-pointer focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
                  aria-label={`Filter by subcategory: ${child.nombre}`}
                />
                <span className="text-sm text-muted-foreground leading-none">
                  {child.nombre}
                </span>
              </label>
            ))}
          </div>
        ))}
      </div>

      {/* Mobile: Dropdown */}
      <div className="md:hidden relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 border border-border rounded-lg bg-card text-left flex items-center justify-between hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 transition-colors"
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <span className="text-sm text-foreground">
            {selectedIds.length > 0 ? `${selectedIds.length} selected` : 'Select categories'}
          </span>
          <ChevronDown
            size={16}
            className={`text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`}
            aria-hidden="true"
          />
        </button>

        {isOpen ? (
          <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
            {hierarchy.parents.map((parent) => (
              <div key={parent.id}>
                <label className="flex items-center gap-2 px-3 py-2 hover:bg-muted/50 cursor-pointer transition-colors">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(parent.id)}
                    onChange={() => handleToggle(parent.id)}
                    className="w-4 h-4 accent-primary rounded border-border cursor-pointer focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
                    aria-label={`Filter by category: ${parent.nombre}`}
                  />
                  <span className="text-sm font-medium text-foreground leading-none">
                    {parent.nombre}
                  </span>
                </label>

                {hierarchy.getChildren(parent.id).map((child) => (
                  <label
                    key={child.id}
                    className="flex items-center gap-2 px-6 py-2 hover:bg-muted/50 cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(child.id)}
                      onChange={() => handleToggle(child.id)}
                      className="w-4 h-4 accent-primary rounded border-border cursor-pointer focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
                      aria-label={`Filter by subcategory: ${child.nombre}`}
                    />
                    <span className="text-sm text-muted-foreground leading-none">
                      {child.nombre}
                    </span>
                  </label>
                ))}
              </div>
            ))}
          </div>
        ) : null}
      </div>

      {/* Clear Button */}
      {selectedIds.length > 0 ? (
        <button
          onClick={handleClearAll}
          className="w-full text-sm text-primary hover:text-primary/80 font-medium py-1 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 rounded"
          aria-label="Clear all category filters"
        >
          Clear All
        </button>
      ) : null}
    </div>
  )
}

export type { CategoryFilterProps }
