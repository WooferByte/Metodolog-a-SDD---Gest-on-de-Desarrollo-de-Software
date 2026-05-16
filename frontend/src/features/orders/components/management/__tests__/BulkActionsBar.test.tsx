/**
 * BulkActionsBar tests.
 *
 * Covers:
 *   - Does NOT render when selectedIds is empty
 *   - Renders with correct count when orders are selected
 *   - "Cambiar estado" button is disabled with aria-disabled when mixed states
 *   - "Cambiar estado" button is enabled when all selected share same status
 *   - "Cancelar seleccionados" button is always present when selection is non-empty
 *   - Clicking the X (clear) button calls clearAll
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BulkActionsBar } from '../BulkActionsBar'
import { useOrdersManagementStore } from '@/features/orders/store/ordersManagementStore'
import type { Order } from '@/features/orders/types'

// Mock useBulkOrderActions
vi.mock('@/features/orders/hooks/useBulkOrderActions', () => ({
  useBulkOrderActions: () => ({
    bulkCancel: vi.fn(),
    bulkAdvanceState: vi.fn(),
  }),
}))

// Mock useUIStore
vi.mock('@/store/uiStore', () => ({
  useUIStore: (selector: (s: { addToast: ReturnType<typeof vi.fn> }) => unknown) =>
    selector({ addToast: vi.fn() }),
}))

// Mock useAdvanceOrderState for StateTransitionModal
vi.mock('@/features/orders/hooks/useAdvanceOrderState', () => ({
  useAdvanceOrderState: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}))

function makeOrder(id: number, estadoId: number): Order {
  return {
    id,
    usuario_id: 1,
    estado_pedido_id: estadoId,
    total: 1000,
    creado_en: '2026-05-15T10:00:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
  } as Order
}

const sampleOrders: Order[] = [
  makeOrder(1, 2),   // CONFIRMADO
  makeOrder(2, 2),   // CONFIRMADO
  makeOrder(3, 3),   // EN_PREPARACIÓN (different)
]

function renderBar(orders = sampleOrders) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <BulkActionsBar orders={orders} />
    </QueryClientProvider>,
  )
}

describe('BulkActionsBar', () => {
  beforeEach(() => {
    useOrdersManagementStore.setState({
      selectedIds: new Set<number>(),
      isBulkPending: false,
    })
    vi.clearAllMocks()
  })

  it('does not render when selectedIds is empty', () => {
    const { container } = renderBar()
    expect(container.firstChild).toBeNull()
  })

  it('renders when at least one order is selected', () => {
    useOrdersManagementStore.setState({ selectedIds: new Set([1]) })
    renderBar()
    expect(screen.getByRole('toolbar')).toBeInTheDocument()
  })

  it('shows correct count for single selection', () => {
    useOrdersManagementStore.setState({ selectedIds: new Set([1]) })
    renderBar()
    expect(screen.getByText('1 pedido seleccionado')).toBeInTheDocument()
  })

  it('shows correct count for multiple selection', () => {
    useOrdersManagementStore.setState({ selectedIds: new Set([1, 2]) })
    renderBar()
    expect(screen.getByText('2 pedidos seleccionados')).toBeInTheDocument()
  })

  it('"Cambiar estado" is disabled with aria-disabled when mixed states', () => {
    // Orders 1 (CONFIRMADO) and 3 (EN_PREPARACIÓN) are selected — mixed states
    useOrdersManagementStore.setState({ selectedIds: new Set([1, 3]) })
    renderBar()
    const btn = screen.getByRole('button', { name: /Cambiar estado/i })
    expect(btn).toBeDisabled()
    expect(btn).toHaveAttribute('aria-disabled', 'true')
  })

  it('"Cambiar estado" is enabled when all selected share same status', () => {
    // Orders 1 and 2 are both CONFIRMADO — same state
    useOrdersManagementStore.setState({ selectedIds: new Set([1, 2]) })
    renderBar()
    const btn = screen.getByRole('button', { name: /Cambiar estado/i })
    expect(btn).not.toBeDisabled()
  })

  it('"Cancelar seleccionados" button is present when selection is non-empty', () => {
    useOrdersManagementStore.setState({ selectedIds: new Set([1]) })
    renderBar()
    expect(screen.getByText('Cancelar seleccionados')).toBeInTheDocument()
  })

  it('clear button calls clearAll on click', () => {
    useOrdersManagementStore.setState({ selectedIds: new Set([1, 2]) })
    renderBar()
    const clearBtn = screen.getByLabelText('Limpiar selección')
    fireEvent.click(clearBtn)
    expect(useOrdersManagementStore.getState().selectedIds.size).toBe(0)
  })
})
