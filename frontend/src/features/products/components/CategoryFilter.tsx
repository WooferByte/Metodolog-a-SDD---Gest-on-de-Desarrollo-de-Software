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
        <div className="h-4 bg-gray-200 rounded animate-pulse" />
        <div className="h-8 bg-gray-200 rounded animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-semibold text-gray-700">
        Categories
      </label>

      {/* Desktop: Always visible */}
      <div className="hidden md:block space-y-2 max-h-64 overflow-y-auto">
        {hierarchy.parents.map((parent) => (
          <div key={parent.id}>
            {/* Parent Category */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedIds.includes(parent.id)}
                onChange={() => handleToggle(parent.id)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                aria-label={`Filter by category: ${parent.nombre}`}
              />
              <span className="font-medium text-gray-700">{parent.nombre}</span>
            </label>

            {/* Child Categories */}
            {hierarchy.getChildren(parent.id).map((child) => (
              <label key={child.id} className="flex items-center gap-2 cursor-pointer ml-6">
                <input
                  type="checkbox"
                  checked={selectedIds.includes(child.id)}
                  onChange={() => handleToggle(child.id)}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                  aria-label={`Filter by subcategory: ${child.nombre}`}
                />
                <span className="text-sm text-gray-600">{child.nombre}</span>
              </label>
            ))}
          </div>
        ))}
      </div>

      {/* Mobile: Dropdown */}
      <div className="md:hidden relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-left flex items-center justify-between hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <span className="text-sm">
            {selectedIds.length > 0 ? `${selectedIds.length} selected` : 'Select categories'}
          </span>
          <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
            {hierarchy.parents.map((parent) => (
              <div key={parent.id}>
                <label className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(parent.id)}
                    onChange={() => handleToggle(parent.id)}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600"
                  />
                  <span className="font-medium text-gray-700 text-sm">{parent.nombre}</span>
                </label>

                {hierarchy.getChildren(parent.id).map((child) => (
                  <label key={child.id} className="flex items-center gap-2 px-6 py-2 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(child.id)}
                      onChange={() => handleToggle(child.id)}
                      className="w-4 h-4 rounded border-gray-300 text-blue-600"
                    />
                    <span className="text-gray-600 text-sm">{child.nombre}</span>
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
          className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium py-1 transition-colors"
          aria-label="Clear all category filters"
        >
          Clear All
        </button>
      )}
    </div>
  )
}

export type { CategoryFilterProps }
