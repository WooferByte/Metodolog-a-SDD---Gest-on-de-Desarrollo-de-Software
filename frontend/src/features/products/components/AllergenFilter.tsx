/**
 * AllergenFilter Component
 * 
 * Checkbox list to exclude products containing specific allergens
 * - Shows allergen names with product count
 * - Multi-select checkboxes
 * - Clear button to remove all filters
 * 
 * @component
 */

import type { AllergenItem } from '@/features/products/hooks'

interface AllergenFilterProps {
  allergens: AllergenItem[]
  selectedIds: string[]
  onChange: (ids: string[]) => void
  isLoading?: boolean
}

/**
 * AllergenFilter Component
 * 
 * @param allergens - List of allergen items with counts
 * @param selectedIds - Array of selected allergen IDs to exclude
 * @param onChange - Callback with new selected IDs
 * @param isLoading - Whether data is loading
 */
export function AllergenFilter({
  allergens,
  selectedIds,
  onChange,
  isLoading = false,
}: AllergenFilterProps) {
  const handleToggle = (allergenId: string) => {
    const newIds = selectedIds.includes(allergenId)
      ? selectedIds.filter((id) => id !== allergenId)
      : [...selectedIds, allergenId]
    onChange(newIds)
  }

  const handleClearAll = () => {
    onChange([])
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        <div className="h-4 bg-muted rounded animate-pulse" />
        <div className="space-y-2">
          {Array(3)
            .fill(0)
            .map((_, i) => (
              <div key={i} className="h-6 bg-muted rounded animate-pulse" />
            ))}
        </div>
      </div>
    )
  }

  if (allergens.length === 0) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-foreground">
          Allergen Exclusions
        </label>
        <p className="text-sm text-muted-foreground">No allergens found in current products</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <fieldset>
        <legend className="text-sm font-semibold text-foreground mb-2">
          Exclude Allergens
        </legend>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {allergens.map((allergen) => (
            <label
              key={allergen.id}
              className="flex items-center gap-2 cursor-pointer hover:bg-muted/50 p-1 rounded transition-colors"
            >
              <input
                type="checkbox"
                checked={selectedIds.includes(allergen.id)}
                onChange={() => handleToggle(allergen.id)}
                className="w-4 h-4 rounded border-border text-red-600 focus:ring-2 focus:ring-red-500"
                aria-label={`Exclude ${allergen.nombre} (found in ${allergen.count} product${allergen.count !== 1 ? 's' : ''})`}
              />
              <span className="text-sm text-foreground flex-1">{allergen.nombre}</span>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                {allergen.count}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      {/* Clear Button */}
      {selectedIds.length > 0 && (
        <button
          onClick={handleClearAll}
          className="w-full text-sm text-red-600 hover:text-red-700 font-medium py-1 transition-colors"
          aria-label="Clear all allergen filters"
        >
          Clear All
        </button>
      )}
    </div>
  )
}

export type { AllergenFilterProps }
