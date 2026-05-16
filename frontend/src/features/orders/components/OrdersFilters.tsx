/**
 * OrdersFilters — filter bar for the admin orders panel.
 *
 * Reads and writes to useOrdersFilterStore (Zustand v5 — client state only).
 * Never stores server data — only UI filter state (design.md D4).
 *
 * Filters:
 *   - Estado select (all ORDER_STATUS_MAP entries + "Todos")
 *   - Search input (by email / user, placeholder)
 *   - Fecha desde / hasta inputs
 *   - "Limpiar filtros" button
 *
 * All inputs have aria-label + htmlFor/id pairs for WCAG AA accessibility.
 */

import { ORDER_STATUS_MAP } from '@/features/orders/constants/orderStatus'
import { useOrdersFilterStore } from '@/features/orders/store/ordersFilterStore'

export function OrdersFilters() {
  const estadoId   = useOrdersFilterStore((s) => s.estadoId)
  const search     = useOrdersFilterStore((s) => s.search)
  const fechaDesde = useOrdersFilterStore((s) => s.fechaDesde)
  const fechaHasta = useOrdersFilterStore((s) => s.fechaHasta)

  const setEstadoId   = useOrdersFilterStore((s) => s.setEstadoId)
  const setSearch     = useOrdersFilterStore((s) => s.setSearch)
  const setFechaDesde = useOrdersFilterStore((s) => s.setFechaDesde)
  const setFechaHasta = useOrdersFilterStore((s) => s.setFechaHasta)
  const resetFilters  = useOrdersFilterStore((s) => s.resetFilters)

  const inputBase =
    'flex h-9 w-full rounded-md border border-border bg-background px-3 py-1 text-sm ' +
    'text-foreground placeholder:text-muted-foreground ' +
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ' +
    'disabled:opacity-50'

  return (
    <div
      className="flex flex-wrap gap-3 items-end pb-4"
      role="search"
      aria-label="Filtros de pedidos"
    >
      {/* Estado select */}
      <div className="flex flex-col gap-1 min-w-[140px]">
        <label
          htmlFor="filter-estado"
          className="text-xs font-medium text-muted-foreground"
        >
          Estado
        </label>
        <select
          id="filter-estado"
          aria-label="Filtrar por estado de pedido"
          value={estadoId ?? ''}
          onChange={(e) =>
            setEstadoId(e.target.value === '' ? null : Number(e.target.value))
          }
          className={inputBase}
        >
          <option value="">Todos</option>
          {Object.values(ORDER_STATUS_MAP).map((meta) => (
            <option key={meta.id} value={meta.id}>
              {meta.label}
            </option>
          ))}
        </select>
      </div>

      {/* Search by email */}
      <div className="flex flex-col gap-1 min-w-[200px] flex-1">
        <label
          htmlFor="filter-search"
          className="text-xs font-medium text-muted-foreground"
        >
          Buscar usuario
        </label>
        <input
          id="filter-search"
          type="search"
          aria-label="Buscar por email de usuario"
          placeholder="email@ejemplo.com"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={inputBase}
        />
      </div>

      {/* Fecha desde */}
      <div className="flex flex-col gap-1 min-w-[150px]">
        <label
          htmlFor="filter-fecha-desde"
          className="text-xs font-medium text-muted-foreground"
        >
          Desde
        </label>
        <input
          id="filter-fecha-desde"
          type="date"
          aria-label="Filtrar desde fecha"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
          className={inputBase}
        />
      </div>

      {/* Fecha hasta */}
      <div className="flex flex-col gap-1 min-w-[150px]">
        <label
          htmlFor="filter-fecha-hasta"
          className="text-xs font-medium text-muted-foreground"
        >
          Hasta
        </label>
        <input
          id="filter-fecha-hasta"
          type="date"
          aria-label="Filtrar hasta fecha"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
          className={inputBase}
        />
      </div>

      {/* Reset button */}
      <button
        type="button"
        onClick={resetFilters}
        aria-label="Limpiar todos los filtros"
        className={
          'h-9 px-3 rounded-md border border-border bg-transparent text-sm text-foreground ' +
          'hover:bg-accent hover:text-accent-foreground ' +
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ' +
          'whitespace-nowrap'
        }
      >
        Limpiar filtros
      </button>
    </div>
  )
}
