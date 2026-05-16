/**
 * OrdersPanelPage — ADMIN/PEDIDOS panel for managing orders.
 *
 * Route: /admin/pedidos (ProtectedRoute, roles: ['PEDIDOS', 'ADMIN'])
 * Loaded via React.lazy in Router.tsx.
 *
 * Features (frontend-orders-management-admin):
 * - OrdersFilters (basic: estado, search, fechaDesde, fechaHasta)
 * - OrderFiltersPanel (advanced: usuarioEmail, totalMin, totalMax — collapsible)
 * - OrdersManagementTable with checkboxes + state change buttons
 * - BulkActionsBar for bulk cancel / bulk state change
 * - StateTransitionModal for per-order state changes
 * - Paginated with keepPreviousData (no flash on page change)
 * - isFetching indicator during background re-fetches
 * - Selection cleared on page change
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOrders } from '@/features/orders/hooks/useOrders'
import { OrdersFilters } from '@/features/orders/components/OrdersFilters'
import { OrderFiltersPanel } from '@/features/orders/components/management/OrderFiltersPanel'
import { OrdersManagementTable } from '@/features/orders/components/management/OrdersManagementTable'
import { BulkActionsBar } from '@/features/orders/components/management/BulkActionsBar'
import { StateTransitionModal } from '@/features/orders/components/management/StateTransitionModal'
import { useOrdersFilterStore } from '@/features/orders/store/ordersFilterStore'
import { useOrdersManagementStore } from '@/features/orders/store/ordersManagementStore'

const LIMIT = 15

export default function OrdersPanelPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)

  // State transition modal — per-order (not bulk)
  const [stateModalOrderId, setStateModalOrderId] = useState<number | null>(null)

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

  // Clear bulk selection when page changes
  const clearAll = useOrdersManagementStore((s) => s.clearAll)
  useEffect(() => {
    clearAll()
  }, [page, clearAll])

  // Find the order for the state modal
  const stateModalOrder = stateModalOrderId != null
    ? orders.find((o) => o.id === stateModalOrderId) ?? null
    : null

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

      {/* Basic filters bar — reads/writes Zustand store */}
      <OrdersFilters />

      {/* Advanced filters panel (collapsible) */}
      <OrderFiltersPanel />

      {/* Bulk actions bar — visible only when ≥1 order selected */}
      <div className="mb-3">
        <BulkActionsBar orders={orders} />
      </div>

      {/* Orders table with management columns */}
      <OrdersManagementTable
        orders={orders}
        isLoading={isLoading}
        onViewDetail={(id) => navigate(`/admin/pedidos/${id}`)}
        onStateChange={(id) => setStateModalOrderId(id)}
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

      {/* Per-order StateTransitionModal */}
      {stateModalOrder != null && (
        <StateTransitionModal
          orderId={stateModalOrder.id}
          currentStatusId={stateModalOrder.estado_pedido_id}
          isOpen={stateModalOrderId != null}
          onClose={() => setStateModalOrderId(null)}
          onSuccess={() => setStateModalOrderId(null)}
        />
      )}
    </main>
  )
}
