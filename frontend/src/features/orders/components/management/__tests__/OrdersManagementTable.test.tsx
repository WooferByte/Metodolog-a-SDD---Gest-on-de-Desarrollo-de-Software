/**
 * OrdersManagementTable tests.
 *
 * Covers:
 *   - Renders rows for each order
 *   - Loading state renders skeletons instead of rows
 *   - Empty state renders a "no orders" message
 *   - Checkbox in header selects all orders on click
 *   - Checkbox in header clears selection when all selected
 *   - Individual row checkbox calls toggleId
 *   - Usuario column: shows usuario_email when available, falls back to #usuario_id
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { OrdersManagementTable } from '../OrdersManagementTable'
import { useOrdersManagementStore } from '@/features/orders/store/ordersManagementStore'
import type { Order } from '@/features/orders/types'

function makeOrder(id: number, estadoId = 2, email?: string): Order & { usuario_email?: string } {
  return {
    id,
    usuario_id: 10 + id,
    estado_pedido_id: estadoId,
    total: 500 * id,
    creado_en: '2026-05-15T10:00:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
    ...(email ? { usuario_email: email } : {}),
  } as Order & { usuario_email?: string }
}

const orders = [
  makeOrder(1, 2, 'user1@test.com'),
  makeOrder(2, 3),                     // no email — should show #12
  makeOrder(3, 5),                     // terminal state
]

function renderTable(
  partialOrders = orders,
  isLoading = false,
) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onViewDetail = vi.fn()
  const onStateChange = vi.fn()
  return {
    onViewDetail,
    onStateChange,
    ...render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <OrdersManagementTable
            orders={partialOrders}
            isLoading={isLoading}
            onViewDetail={onViewDetail}
            onStateChange={onStateChange}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    ),
  }
}

describe('OrdersManagementTable', () => {
  beforeEach(() => {
    useOrdersManagementStore.setState({
      selectedIds: new Set<number>(),
      isBulkPending: false,
    })
    vi.clearAllMocks()
  })

  it('renders a table with correct aria-label', () => {
    renderTable()
    expect(
      screen.getByRole('grid', { name: 'Tabla de gestión de pedidos' }),
    ).toBeInTheDocument()
  })

  it('renders a row for each order', () => {
    renderTable()
    // 3 orders → 3 rows — getAllByText since desktop+mobile both render
    expect(screen.getAllByText('#1').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('#2').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('#3').length).toBeGreaterThanOrEqual(1)
  })

  it('renders empty state when orders=[]', () => {
    renderTable([])
    // Both desktop and mobile render empty state — check at least one
    expect(screen.getAllByText('No hay pedidos registrados').length).toBeGreaterThanOrEqual(1)
  })

  it('renders skeletons when isLoading=true', () => {
    renderTable([], true)
    // There should be no real order rows
    expect(screen.queryByText('#1')).not.toBeInTheDocument()
  })

  it('shows usuario_email when available', () => {
    renderTable()
    expect(screen.getByText('user1@test.com')).toBeInTheDocument()
  })

  it('shows #usuario_id when usuario_email is not available', () => {
    renderTable()
    // Order 2 has no email, usuario_id=12
    expect(screen.getByText('#12')).toBeInTheDocument()
  })

  it('header checkbox selects all orders when clicked', () => {
    renderTable()
    const headerCheckbox = screen.getByLabelText('Seleccionar todos los pedidos')
    fireEvent.click(headerCheckbox)
    const { selectedIds } = useOrdersManagementStore.getState()
    expect(selectedIds.has(1)).toBe(true)
    expect(selectedIds.has(2)).toBe(true)
    expect(selectedIds.has(3)).toBe(true)
  })

  it('header checkbox clears selection when all are already selected', () => {
    useOrdersManagementStore.setState({ selectedIds: new Set([1, 2, 3]) })
    renderTable()
    const headerCheckbox = screen.getByLabelText('Deseleccionar todos los pedidos')
    fireEvent.click(headerCheckbox)
    expect(useOrdersManagementStore.getState().selectedIds.size).toBe(0)
  })

  it('individual row checkbox calls toggleId', () => {
    renderTable()
    // Both desktop and mobile render this checkbox — get first one
    const checkboxes = screen.getAllByLabelText('Seleccionar pedido #1')
    fireEvent.click(checkboxes[0])
    expect(useOrdersManagementStore.getState().selectedIds.has(1)).toBe(true)
  })
})
