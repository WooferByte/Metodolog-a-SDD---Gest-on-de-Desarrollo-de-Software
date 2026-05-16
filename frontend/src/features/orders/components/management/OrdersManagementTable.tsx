/**
 * OrdersManagementTable — full-featured table for admin order management.
 *
 * Columns: [checkbox] | # Pedido | Fecha | Total | Estado | Usuario | Acciones
 *
 * Header checkbox:
 *   - Uses a ref to set indeterminate property when partially selected
 *   - Clicking checks all visible orders (setAllIds) or clears (clearAll)
 *
 * Row behavior:
 *   - Each row has its own checkbox from OrdersManagementRow
 *   - onStateChange triggers the StateTransitionModal in the parent
 *
 * Responsive:
 *   - Table: hidden md:block (desktop only)
 *   - Mobile: block md:hidden → renders OrderCard list with inline actions
 *
 * Loading: renders OrdersSkeleton rows with extra columns count.
 * Empty state: single colSpan row.
 *
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { OrdersManagementRow } from '@/features/orders/components/management/OrdersManagementRow'
import { OrderCard } from '@/features/orders/components/OrderCard'
import { useOrdersManagementStore } from '@/features/orders/store/ordersManagementStore'
import type { Order } from '@/features/orders/types'

export interface OrdersManagementTableProps {
  orders: Order[]
  isLoading: boolean
  onViewDetail: (id: number) => void
  onStateChange: (id: number) => void
}

/** Skeleton row with 7 columns (checkbox + 6 data) */
function ManagementSkeletonRow() {
  return (
    <tr className="animate-pulse border-b border-border">
      {/* Checkbox */}
      <td className="px-4 py-3">
        <div className="h-4 w-4 rounded bg-muted" />
      </td>
      {/* # Pedido */}
      <td className="px-4 py-3">
        <div className="h-4 w-16 rounded bg-muted" />
      </td>
      {/* Fecha */}
      <td className="px-4 py-3">
        <div className="h-4 w-32 rounded bg-muted" />
      </td>
      {/* Total */}
      <td className="px-4 py-3">
        <div className="h-4 w-20 rounded bg-muted ml-auto" />
      </td>
      {/* Estado */}
      <td className="px-4 py-3">
        <div className="h-5 w-24 rounded-full bg-muted" />
      </td>
      {/* Usuario */}
      <td className="px-4 py-3">
        <div className="h-4 w-40 rounded bg-muted" />
      </td>
      {/* Acciones */}
      <td className="px-4 py-3">
        <div className="flex gap-2 justify-center">
          <div className="h-8 w-12 rounded-lg bg-muted" />
          <div className="h-8 w-16 rounded-lg bg-muted" />
        </div>
      </td>
    </tr>
  )
}

export function OrdersManagementTable({
  orders,
  isLoading,
  onViewDetail,
  onStateChange,
}: OrdersManagementTableProps) {
  const headerCheckboxRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const selectedIds      = useOrdersManagementStore((s) => s.selectedIds)
  const setAllIds        = useOrdersManagementStore((s) => s.setAllIds)
  const clearAll         = useOrdersManagementStore((s) => s.clearAll)
  const isAllSelected    = useOrdersManagementStore((s) => s.isAllSelected)
  const isIndeterminate  = useOrdersManagementStore((s) => s.isIndeterminate)

  const orderIds = orders.map((o) => o.id)
  const allSelected   = isAllSelected(orderIds)
  const indeterminate = isIndeterminate(orderIds)

  // Set the native indeterminate property — this cannot be done via JSX props
  useEffect(() => {
    if (headerCheckboxRef.current) {
      headerCheckboxRef.current.indeterminate = indeterminate
    }
  }, [indeterminate])

  const handleHeaderCheckbox = () => {
    if (allSelected || indeterminate) {
      clearAll()
    } else {
      setAllIds(orderIds)
    }
  }

  const SKELETON_COUNT = 5

  return (
    <>
      {/* ── Desktop table (hidden on mobile) ─────────────────── */}
      <div className="hidden md:block w-full overflow-x-auto rounded-xl border border-border">
        <table
          role="grid"
          className="w-full border-collapse text-sm"
          aria-label="Tabla de gestión de pedidos"
          aria-rowcount={orders.length}
        >
          <thead>
            <tr className="border-b border-border bg-muted/50">
              {/* Checkbox header */}
              <th scope="col" className="px-4 py-3 w-10">
                <input
                  ref={headerCheckboxRef}
                  type="checkbox"
                  checked={allSelected}
                  onChange={handleHeaderCheckbox}
                  aria-label={allSelected ? 'Deseleccionar todos los pedidos' : 'Seleccionar todos los pedidos'}
                  disabled={isLoading || orders.length === 0}
                  className="h-4 w-4 rounded border-border accent-primary cursor-pointer disabled:opacity-50"
                />
              </th>

              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                # Pedido
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Fecha
              </th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Total
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Estado
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Usuario
              </th>
              <th scope="col" className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Acciones
              </th>
            </tr>
          </thead>

          <tbody>
            {isLoading ? (
              Array.from({ length: SKELETON_COUNT }, (_, i) => (
                <ManagementSkeletonRow key={i} />
              ))
            ) : orders.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-12 text-center text-sm text-muted-foreground"
                >
                  No hay pedidos registrados
                </td>
              </tr>
            ) : (
              orders.map((order) => (
                <OrdersManagementRow
                  key={order.id}
                  order={order}
                  onViewDetail={onViewDetail}
                  onStateChange={onStateChange}
                />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Mobile list (shown only below md breakpoint) ──────── */}
      <div className="block md:hidden space-y-3">
        {isLoading ? (
          Array.from({ length: SKELETON_COUNT }, (_, i) => (
            <div key={i} className="animate-pulse rounded-xl border border-border bg-card p-4 space-y-3">
              <div className="flex justify-between">
                <div className="h-5 w-24 rounded-full bg-muted" />
                <div className="h-4 w-20 rounded bg-muted" />
              </div>
              <div className="h-4 w-32 rounded bg-muted" />
              <div className="flex justify-between">
                <div className="h-5 w-16 rounded bg-muted" />
                <div className="h-8 w-24 rounded-lg bg-muted" />
              </div>
            </div>
          ))
        ) : orders.length === 0 ? (
          <p className="py-12 text-center text-sm text-muted-foreground">
            No hay pedidos registrados
          </p>
        ) : (
          orders.map((order) => {
            const isSelected = selectedIds.has(order.id)
            const toggleId = useOrdersManagementStore.getState().toggleId
            return (
              <div key={order.id} className="relative">
                {/* Selection indicator */}
                <div className="absolute top-3 right-3 z-10">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleId(order.id)}
                    aria-label={`Seleccionar pedido #${order.id}`}
                    className="h-4 w-4 rounded border-border accent-primary cursor-pointer"
                  />
                </div>
                <OrderCard
                  order={order}
                  mode="admin"
                  onViewDetail={() => navigate(`/admin/pedidos/${order.id}`)}
                />
              </div>
            )
          })
        )}
      </div>
    </>
  )
}
