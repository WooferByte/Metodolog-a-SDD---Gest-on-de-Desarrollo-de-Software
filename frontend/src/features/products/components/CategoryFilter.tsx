/**
 * CategoryFilter Component
 * 
 * Multi-select category dropdown with hierarchical structure
 * - Displays parent and child categories
 * - Multi-select with checkboxes
 * - Collapsible on mobile
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
export function CategoryFilter({
  selectedIds,
  onChange,
}: CategoryFilterProps) {
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
    <div className="space-y-2">
      {/* Section heading — semantic h3 instead of label */}
      <h3 className="text-sm font-semibold text-foreground mb-3">
        Categories
      </h3>

      {/* Desktop: Always visible list */}
      <div className="hidden md:block space-y-2 max-h-64 overflow-y-auto">
        {hierarchy.parents.map((parent) => (
          <div key={parent.id}>
            {/* Parent Category */}
            <label className="flex items-center gap-2 cursor-pointer hover:bg-muted/50 rounded px-1 py-0.5 transition-colors">
              <input
                type="checkbox"
                checked={selectedIds.includes(parent.id)}
                onChange={() => handleToggle(parent.id)}
                className="w-4 h-4 accent-primary rounded border-border focus:ring-2 focus:ring-ring focus:ring-offset-1"
                aria-label={`Filter by category: ${parent.nombre}`}
              />
              <span className="font-medium text-foreground text-sm">{parent.nombre}</span>
            </label>

            {/* Child Categories */}
            {hierarchy.getChildren(parent.id).map((child) => (
              <label key={child.id} className="flex items-center gap-2 cursor-pointer ml-6 hover:bg-muted/50 rounded px-1 py-0.5 transition-colors">
                <input
                  type="checkbox"
                  checked={selectedIds.includes(child.id)}
                  onChange={() => handleToggle(child.id)}
                  className="w-4 h-4 accent-primary rounded border-border focus:ring-2 focus:ring-ring focus:ring-offset-1"
                  aria-label={`Filter by subcategory: ${child.nombre}`}
                />
                <span className="text-sm text-muted-foreground">{child.nombre}</span>
              </label>
            ))}
          </div>
        ))}
      </div>

      {/* Mobile: Dropdown */}
      <div className="md:hidden relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 border border-border rounded-lg bg-card text-left flex items-center justify-between hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1 transition-colors"
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <span className="text-sm text-foreground">
            {selectedIds.length > 0 ? `${selectedIds.length} selected` : 'Select categories'}
          </span>
          <ChevronDown size={16} className={`text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
            {hierarchy.parents.map((parent) => (
              <div key={parent.id}>
                <label className="flex items-center gap-2 px-3 py-2 hover:bg-muted/50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(parent.id)}
                    onChange={() => handleToggle(parent.id)}
                    className="w-4 h-4 accent-primary rounded border-border focus:ring-2 focus:ring-ring focus:ring-offset-1"
                    aria-label={`Filter by category: ${parent.nombre}`}
                  />
                  <span className="font-medium text-foreground text-sm">{parent.nombre}</span>
                </label>

                {hierarchy.getChildren(parent.id).map((child) => (
                  <label key={child.id} className="flex items-center gap-2 px-6 py-2 hover:bg-muted/50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(child.id)}
                      onChange={() => handleToggle(child.id)}
                      className="w-4 h-4 accent-primary rounded border-border focus:ring-2 focus:ring-ring focus:ring-offset-1"
                      aria-label={`Filter by subcategory: ${child.nombre}`}
                    />
                    <span className="text-muted-foreground text-sm">{child.nombre}</span>
                  </label>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Clear Button */}
      {selectedIds.length > 0 && (
        <button
          onClick={handleClearAll}
          className="w-full text-sm text-primary hover:text-primary/80 font-medium py-1 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
          aria-label="Clear all category filters"
        >
          Clear All
        </button>
      )}
    </div>
  )
}

export type { CategoryFilterProps }
