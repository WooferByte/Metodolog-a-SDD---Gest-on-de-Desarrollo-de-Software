/**
 * SearchInput Component
 * 
 * Real-time search input with debounce
 * - Debounced onChange (250ms) to avoid excessive API calls
 * - Labeled for accessibility
 * - Clear button to reset search
 * 
 * @component
 */

import { useEffect, useState } from 'react'
import { Search, X } from 'lucide-react'
import { SEARCH_DEBOUNCE_DELAY } from '@/features/products/constants'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

/**
 * SearchInput Component
 * 
 * @param value - Current search value
 * @param onChange - Debounced callback with new search value
 * @param placeholder - Input placeholder text
 */
export function SearchInput({
  value,
  onChange,
  placeholder = 'Search products...',
}: SearchInputProps) {
  const [localValue, setLocalValue] = useState(value)

  // Debounce effect
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue)
    }, SEARCH_DEBOUNCE_DELAY)

    return () => clearTimeout(timer)
  }, [localValue, onChange])

  // Sync external value changes
  useEffect(() => {
    setLocalValue(value)
  }, [value])

  const handleClear = () => {
    setLocalValue('')
  }

  return (
    <div className="relative w-full">
      <label htmlFor="search-input" className="sr-only">
        Search products
      </label>
      <div className="relative">
        <Search
          size={20}
          className="absolute left-3 top-3 text-muted-foreground pointer-events-none"
          aria-hidden="true"
        />
        <input
          id="search-input"
          type="text"
          value={localValue}
          onChange={(e) => setLocalValue(e.currentTarget.value)}
          placeholder={placeholder}
          className="w-full pl-10 pr-10 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
          aria-label="Search products by name or description"
          aria-describedby="search-debounce-info"
        />
        {localValue && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-3 text-muted-foreground hover:text-muted-foreground transition-colors"
            aria-label="Clear search"
            title="Clear search"
          >
            <X size={20} />
          </button>
        )}
      </div>
      <p id="search-debounce-info" className="sr-only">
        Search updates after you stop typing
      </p>
    </div>
  )
}

export type { SearchInputProps }
