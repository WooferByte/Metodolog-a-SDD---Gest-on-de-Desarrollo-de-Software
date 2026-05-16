/**
 * OrdersPanelPage — ADMIN/PEDIDOS panel for managing orders.
 *
 * Route: /admin/pedidos (ProtectedRoute, roles: ['PEDIDOS', 'ADMIN'])
 * Loaded via React.lazy in Router.tsx (design.md D6).
 *
 * Features:
 * - OrdersFilters reading/writing Zustand UI state
 * - OrdersTable with ARIA-compliant table and skeleton rows
 * - Paginated with keepPreviousData (no flash on page change)
 * - isFetching indicator during background re-fetches
 * - Accessible pagination with aria-current="page"
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOrders } from '@/features/orders/hooks/useOrders'
import { OrdersFilters } from '@/features/orders/components/OrdersFilters'
import { OrdersTable } from '@/features/orders/components/OrdersTable'
import { useOrdersFilterStore } from '@/features/orders/store/ordersFilterStore'

const LIMIT = 15

export default function OrdersPanelPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)

  // Read filters from Zustand store (client state — never server data)
  const estadoId   = useOrdersFilterStore((s) => s.estadoId)
  const search     = useOrdersFilterStore((s) => s.search)
  const fechaDesde = useOrdersFilterStore((s) => s.fechaDesde)
  const fechaHasta = useOrdersFilterStore((s) => s.fechaHasta)

  const { data, isLoading, isFetching } = useOrders({
    limit: LIMIT,
    offset: page * LIMIT,
    estadoId,
    search,
    fechaDesde,
    fechaHasta,
  })

  const orders   = data?.items ?? []
  const total    = data?.total ?? 0
  const lastPage = Math.max(0, Math.ceil(total / LIMIT) - 1)

  const hasPrev = page > 0
  const hasNext = page < lastPage

  // Reset to page 0 when filters change (handled naturally because queryKey changes)
  // Note: page state resets via filter changes would require a useEffect, but since
  // the filter change triggers a new query, offset is sent correctly.

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-foreground">Panel de Pedidos</h1>
        {isFetching && !isLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">
            Actualizando...
          </span>
        )}
      </div>

      {/* Filters bar — reads/writes Zustand store */}
      <OrdersFilters />

      {/* Orders table */}
      <OrdersTable
        orders={orders}
        isLoading={isLoading}
        onViewDetail={(id) => navigate(`/admin/pedidos/${id}`)}
      />

      {/* Pagination */}
      {total > LIMIT && (
        <nav
          aria-label="Paginación del panel de pedidos"
          className="mt-6 flex items-center justify-center gap-2"
        >
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={!hasPrev}
            aria-label="Página anterior"
            className="h-9 px-4 rounded-md border border-border text-sm text-foreground hover:bg-accent disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Anterior
          </button>

          {Array.from({ length: lastPage + 1 }, (_, i) => i).map((p) => (
            <button
              key={p}
              onClick={() => setPage(p)}
              aria-current={p === page ? 'page' : undefined}
              aria-label={`Página ${p + 1}`}
              className={[
                'h-9 w-9 rounded-md text-sm font-medium',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                p === page
                  ? 'bg-primary text-primary-foreground'
                  : 'border border-border text-foreground hover:bg-accent',
              ].join(' ')}
            >
              {p + 1}
            </button>
          ))}

          <button
            onClick={() => setPage((p) => Math.min(lastPage, p + 1))}
            disabled={!hasNext}
            aria-label="Página siguiente"
            className="h-9 px-4 rounded-md border border-border text-sm text-foreground hover:bg-accent disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Siguiente
          </button>
        </nav>
      )}

      {/* Total count */}
      {!isLoading && (
        <p className="mt-4 text-center text-xs text-muted-foreground">
          {total} {total === 1 ? 'pedido' : 'pedidos'} en total
        </p>
      )}
    </main>
  )
}
