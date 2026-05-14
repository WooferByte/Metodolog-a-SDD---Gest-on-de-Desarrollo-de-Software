/**
 * AllergenFilter Component
 *
 * Checkbox list to exclude products containing specific allergens.
 * Visually differentiated from CategoryFilter with a warning-tinted heading badge.
 *
 * Tokens: only semantic @theme tokens — no raw hex or Tailwind color scales.
 * Accessibility: WCAG AA — each checkbox wrapped in <label> for full click area,
 * fieldset+legend for group semantics.
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
 * @param allergens - List of allergen items with product counts
 * @param selectedIds - Array of selected allergen IDs to exclude
 * @param onChange - Callback with new selected IDs
 * @param isLoading - Whether allergen data is loading
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
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-6 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (allergens.length === 0) {
    return (
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
          Allergen Exclusions
        </h3>
        <p className="text-sm text-muted-foreground">No allergens found in current products</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <fieldset>
        {/* Legend acts as the visual heading for this group */}
        <div className="flex items-center gap-2 mb-3">
          <legend className="text-sm font-semibold text-foreground uppercase tracking-wide">
            Allergen Exclusions
          </legend>
          <span className="text-xs text-warning bg-warning/10 rounded px-2 py-0.5 font-medium">
            Exclude
          </span>
        </div>

        <div className="space-y-0.5 max-h-48 overflow-y-auto">
          {allergens.map((allergen) => (
            <label
              key={allergen.id}
              className="flex items-center gap-2 hover:bg-muted/50 rounded-md px-2 py-1.5 -mx-2 cursor-pointer transition-colors"
            >
              <input
                type="checkbox"
                checked={selectedIds.includes(allergen.id)}
                onChange={() => handleToggle(allergen.id)}
                className="w-4 h-4 accent-primary rounded border-border cursor-pointer focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
                aria-label={`Exclude ${allergen.nombre} (found in ${allergen.count} product${allergen.count !== 1 ? 's' : ''})`}
              />
              <span className="text-sm text-foreground leading-none flex-1">
                {allergen.nombre}
              </span>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                {allergen.count}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      {/* Clear Button */}
      {selectedIds.length > 0 ? (
        <button
          onClick={handleClearAll}
          className="w-full text-sm text-destructive hover:text-destructive/80 font-medium py-1 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 rounded"
          aria-label="Clear all allergen filters"
        >
          Clear All
        </button>
      ) : null}
    </div>
  )
}

export type { AllergenFilterProps }
