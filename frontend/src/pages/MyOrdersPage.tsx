/**
 * MyOrdersPage — CLIENT timeline view of their own orders.
 *
 * Route: /mis-pedidos (ProtectedRoute, roles: ['CLIENT', 'ADMIN'])
 * Loaded via React.lazy in Router.tsx (design.md D6).
 *
 * Features:
 * - Paginated orders list (10 per page) with keepPreviousData
 * - OrdersSkeleton (mode="client") during initial load
 * - Empty state with link to catalog
 * - isFetching indicator (subtle pulsing border) during background re-fetches
 * - Responsive: 1 column (mobile) / 2 columns (sm+)
 * - Accessible pagination with aria-current="page" and aria-label on nav
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useOrders } from '@/features/orders/hooks/useOrders'
import { OrderCard } from '@/features/orders/components/OrderCard'
import { OrdersSkeleton } from '@/features/orders/components/OrdersSkeleton'

const LIMIT = 10

export default function MyOrdersPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)  // 0-based page index

  const { data, isLoading, isFetching } = useOrders({
    limit: LIMIT,
    offset: page * LIMIT,
  })

  const orders   = data?.items ?? []
  const total    = data?.total ?? 0
  const lastPage = Math.max(0, Math.ceil(total / LIMIT) - 1)

  const hasPrev = page > 0
  const hasNext = page < lastPage

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-foreground">Mis Pedidos</h1>
        {isFetching && !isLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">
            Actualizando...
          </span>
        )}
      </div>

      {/* Loading state */}
      {isLoading ? (
        <OrdersSkeleton mode="client" count={5} />
      ) : orders.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <p className="text-muted-foreground text-sm">
            No tenés pedidos todavía.
          </p>
          <Link
            to="/productos"
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Ir al catálogo
          </Link>
        </div>
      ) : (
        <>
          {/* Orders grid — 1 col mobile, 2 cols sm+ */}
          <div
            className={[
              'grid gap-4',
              'grid-cols-1 sm:grid-cols-2',
              // Subtle border pulse when re-fetching in background
              isFetching ? 'ring-1 ring-border rounded-xl' : '',
            ].join(' ')}
          >
            {orders.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                mode="client"
                onViewDetail={(id) => navigate(`/orders/${id}`)}
              />
            ))}
          </div>

          {/* Pagination */}
          {total > LIMIT && (
            <nav
              aria-label="Paginación de pedidos"
              className="mt-8 flex items-center justify-center gap-2"
            >
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={!hasPrev}
                aria-label="Página anterior"
                className="h-9 px-4 rounded-md border border-border text-sm text-foreground hover:bg-accent disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                Anterior
              </button>

              {/* Page numbers */}
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
        </>
      )}
    </main>
  )
}
