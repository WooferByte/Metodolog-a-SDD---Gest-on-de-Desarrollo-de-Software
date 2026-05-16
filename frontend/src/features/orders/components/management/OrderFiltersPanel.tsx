/**
 * OrderFiltersPanel — advanced filters panel for the admin orders management view.
 *
 * Extends basic filters (existing OrdersFilters) with:
 *   - totalMin / totalMax: price range filter
 *
 * Email search is already handled by OrdersFilters — not duplicated here.
 *
 * Uses a collapsible <details> element so the panel is hidden by default.
 * Reads/writes to useOrdersFilterStore (client state — never server data).
 */

import { useOrdersFilterStore } from '@/features/orders/store/ordersFilterStore'

const inputBase =
  'flex h-9 w-full rounded-md border border-border bg-background px-3 py-1 text-sm ' +
  'text-foreground placeholder:text-muted-foreground ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ' +
  'disabled:opacity-50'

export function OrderFiltersPanel() {
  const totalMin = useOrdersFilterStore((s) => s.totalMin)
  const totalMax = useOrdersFilterStore((s) => s.totalMax)

  const setTotalMin  = useOrdersFilterStore((s) => s.setTotalMin)
  const setTotalMax  = useOrdersFilterStore((s) => s.setTotalMax)
  const resetFilters = useOrdersFilterStore((s) => s.resetFilters)

  const rangeInvalid =
    totalMin !== null && totalMax !== null && totalMin > totalMax

  const hasActiveFilters = totalMin !== null || totalMax !== null

  return (
    <details className="mb-4 rounded-xl border border-border bg-background overflow-hidden">
      <summary
        className={[
          'flex cursor-pointer items-center justify-between px-4 py-3',
          'text-sm font-medium text-foreground',
          'hover:bg-accent/50 transition-colors list-none',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring',
        ].join(' ')}
        aria-label="Filtros avanzados de pedidos"
      >
        <span>
          Filtros avanzados
          {hasActiveFilters && (
            <span className="ml-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-xs font-semibold text-primary-foreground">
              {[totalMin !== null ? 1 : 0, totalMax !== null ? 1 : 0].reduce((a, b) => a + b, 0)}
            </span>
          )}
        </span>
        <span className="text-muted-foreground text-xs">Expandir</span>
      </summary>

      <div className="border-t border-border px-4 py-4">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Total mínimo */}
          <div className="flex flex-col gap-1 min-w-[130px]">
            <label
              htmlFor="adv-filter-total-min"
              className="text-xs font-medium text-muted-foreground"
            >
              Total mínimo ($)
            </label>
            <input
              id="adv-filter-total-min"
              type="number"
              min="0"
              step="0.01"
              aria-label="Filtrar por monto mínimo del pedido"
              placeholder="0.00"
              value={totalMin ?? ''}
              onChange={(e) =>
                setTotalMin(e.target.value === '' ? null : Number(e.target.value))
              }
              className={inputBase}
            />
          </div>

          {/* Total máximo */}
          <div className="flex flex-col gap-1 min-w-[130px]">
            <label
              htmlFor="adv-filter-total-max"
              className="text-xs font-medium text-muted-foreground"
            >
              Total máximo ($)
            </label>
            <input
              id="adv-filter-total-max"
              type="number"
              min="0"
              step="0.01"
              aria-label="Filtrar por monto máximo del pedido"
              placeholder="9999.99"
              value={totalMax ?? ''}
              onChange={(e) =>
                setTotalMax(e.target.value === '' ? null : Number(e.target.value))
              }
              className={[
                inputBase,
                rangeInvalid ? 'border-destructive focus-visible:ring-destructive' : '',
              ].join(' ')}
              aria-invalid={rangeInvalid}
              aria-describedby={rangeInvalid ? 'adv-filter-range-error' : undefined}
            />
          </div>

          {/* Reset button */}
          <button
            type="button"
            onClick={resetFilters}
            aria-label="Limpiar todos los filtros incluyendo avanzados"
            className={[
              'h-9 px-3 rounded-md border border-border bg-transparent text-sm text-foreground',
              'hover:bg-accent hover:text-accent-foreground',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              'whitespace-nowrap',
            ].join(' ')}
          >
            Limpiar filtros
          </button>
        </div>

        {/* Range validation error */}
        {rangeInvalid && (
          <p
            id="adv-filter-range-error"
            role="alert"
            className="mt-2 text-xs text-destructive"
          >
            El monto mínimo no puede ser mayor al máximo.
          </p>
        )}
      </div>
    </details>
  )
}
