/**
 * OrderDetailPage — page component for viewing a single order's detail.
 *
 * Routes:
 *   /pedidos/:id          → CLIENT view (ownership enforced by backend)
 *   /admin/pedidos/:id    → Admin view (adminMode=true, access to any order)
 *
 * Design decision D6 (design.md): Single page with adminMode prop — same visual
 * structure, only OrderActions changes behavior based on the prop.
 *
 * Loading: OrderDetailSkeleton while data is fetching.
 * Error: error state with CTA to go back to order listing.
 * Invalid ID: redirects to /404.
 *
 * This file is loaded via React.lazy in the router for code splitting.
 */

import { useParams, useNavigate, Link } from 'react-router-dom'
import { OrderDetailHeader } from '@/features/orders/components/detail/OrderDetailHeader'
import { OrderItemSnapshot } from '@/features/orders/components/detail/OrderItemSnapshot'
import { OrderTimeline } from '@/features/orders/components/detail/OrderTimeline'
import { OrderActions } from '@/features/orders/components/detail/OrderActions'
import { CancelOrderModal } from '@/features/orders/components/detail/CancelOrderModal'
import { OrderDetailSkeleton } from '@/features/orders/components/detail/OrderDetailSkeleton'
import { useOrderDetail } from '@/features/orders/hooks/useOrderDetail'
import { cn } from '@/shared/lib/utils'

export interface OrderDetailPageProps {
  adminMode?: boolean
}

export default function OrderDetailPage({ adminMode = false }: OrderDetailPageProps) {
  const { id: rawId } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // Parse and validate the ID param
  const orderId = rawId ? parseInt(rawId, 10) : NaN

  // Redirect to 404 if ID is not a valid positive integer
  if (isNaN(orderId) || orderId <= 0) {
    navigate('/404', { replace: true })
    return null
  }

  const { data: order, isLoading, isError, error } = useOrderDetail(orderId)

  // Loading state
  if (isLoading) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-6 md:px-6">
        <OrderDetailSkeleton />
      </main>
    )
  }

  // Error state
  if (isError || !order) {
    const backPath = adminMode ? '/admin/pedidos' : '/orders'
    const backLabel = adminMode ? 'Volver al panel de pedidos' : 'Volver a mis pedidos'

    return (
      <main className="mx-auto max-w-2xl px-4 py-6 md:px-6">
        <div
          role="alert"
          className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-8 text-center"
        >
          {/* Error icon */}
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <svg
              className="h-6 w-6 text-destructive"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>

          <div className="flex flex-col gap-1">
            <h1 className="text-lg font-semibold text-foreground">
              No se pudo cargar el pedido
            </h1>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error
                ? error.message
                : 'El pedido no existe o no tenés permiso para verlo.'}
            </p>
          </div>

          <Link
            to={backPath}
            className={cn(
              'inline-flex items-center justify-center gap-2 font-medium',
              'transition-colors duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-ring',
              'border border-border bg-transparent text-foreground',
              'hover:bg-accent hover:text-accent-foreground',
              'h-10 px-4 text-sm rounded-lg',
            )}
          >
            {backLabel}
          </Link>
        </div>
      </main>
    )
  }

  // Render the full detail page
  return (
    <main className="mx-auto max-w-2xl px-4 py-6 md:px-6">
      {/* Back navigation */}
      <nav aria-label="Navegación de regreso" className="mb-4">
        <Link
          to={adminMode ? '/admin/pedidos' : '/orders'}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          aria-label={adminMode ? 'Volver al panel de pedidos' : 'Volver a mis pedidos'}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          {adminMode ? 'Panel de pedidos' : 'Mis pedidos'}
        </Link>
      </nav>

      {/* Page sections */}
      <div className="flex flex-col gap-4">
        {/* Header: status, date, total, address */}
        <OrderDetailHeader order={order} />

        {/* Line items */}
        {order.detalles.length > 0 && (
          <section aria-labelledby="items-heading">
            <div className="rounded-xl border border-border bg-card p-4 md:p-6">
              <h2
                id="items-heading"
                className="mb-3 text-base font-semibold text-foreground"
              >
                Productos
              </h2>
              <div className="flex flex-col gap-3">
                {order.detalles.map((item) => (
                  <OrderItemSnapshot key={item.id} item={item} />
                ))}
              </div>
            </div>
          </section>
        )}

        {/* FSM timeline */}
        {order.historial && order.historial.length > 0 && (
          <section aria-labelledby="timeline-heading">
            <div id="timeline-heading" className="sr-only">
              Historial de estados
            </div>
            <OrderTimeline historial={order.historial} />
          </section>
        )}

        {/* Actions: cancel (CLIENT) or advance state (admin) */}
        <section aria-labelledby="actions-heading">
          <div id="actions-heading" className="sr-only">
            Acciones disponibles
          </div>
          <OrderActions order={order} adminMode={adminMode} />
        </section>
      </div>

      {/* Cancel confirmation modal — only rendered when CLIENT, controlled by Zustand store */}
      {!adminMode && <CancelOrderModal orderId={orderId} />}
    </main>
  )
}
