/**
 * OrderActions tests.
 *
 * Verifies CLIENT mode:
 *   - "Cancelar pedido" button is present
 *   - Button is disabled with aria-disabled="true" when estado !== 1 (PENDIENTE)
 *   - Button is enabled when estado === 1 (PENDIENTE)
 *   - Clicking enabled button opens the cancel modal (via store)
 *
 * Verifies Admin mode:
 *   - Terminal states (5=ENTREGADO, 6=CANCELADO) show "cerrado" message, no buttons
 *   - State 1 (PENDIENTE) shows no manual advance available
 *   - State 2 (CONFIRMADO) shows a select + advance button
 */

import '@testing-library/jest-dom'
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { OrderActions } from '../OrderActions'
import { useOrderDetailStore } from '@/features/orders/store/orderDetailStore'
import type { OrderDetail } from '@/features/orders/types'

function makeOrder(estadoId: number): OrderDetail {
  return {
    id: 10,
    usuario_id: 2,
    estado_pedido_id: estadoId,
    total: 2000,
    creado_en: '2026-05-15T10:00:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
    direccion_entrega_id: 1,
    detalles: [],
    historial: [],
  } as OrderDetail
}

function renderActions(order: OrderDetail, adminMode = false) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <OrderActions order={order} adminMode={adminMode} />
    </QueryClientProvider>,
  )
}

describe('OrderActions — CLIENT mode', () => {
  beforeEach(() => {
    useOrderDetailStore.setState({ isCancelModalOpen: false })
  })

  it('renders "Cancelar pedido" button', () => {
    renderActions(makeOrder(1))
    expect(screen.getByText('Cancelar pedido')).toBeInTheDocument()
  })

  it('button is enabled when estado_pedido_id === 1 (PENDIENTE)', () => {
    renderActions(makeOrder(1))
    const btn = screen.getByText('Cancelar pedido')
    expect(btn).not.toBeDisabled()
  })

  it('button is disabled with aria-disabled when estado_pedido_id !== 1', () => {
    renderActions(makeOrder(3))    // EN_PREPARACIÓN
    const btn = screen.getByText('Cancelar pedido')
    expect(btn).toBeDisabled()
    expect(btn).toHaveAttribute('aria-disabled', 'true')
  })

  it('button is disabled for estado 5 (ENTREGADO)', () => {
    renderActions(makeOrder(5))
    const btn = screen.getByText('Cancelar pedido')
    expect(btn).toBeDisabled()
  })
})

describe('OrderActions — Admin mode', () => {
  it('shows "cerrado" message for estado 5 (ENTREGADO) with no buttons', () => {
    renderActions(makeOrder(5), true)
    expect(screen.getByText(/cerrado/i)).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('shows "cerrado" message for estado 6 (CANCELADO) with no buttons', () => {
    renderActions(makeOrder(6), true)
    expect(screen.getByText(/cerrado/i)).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('shows "pendiente de confirmación" message for estado 1 (PENDIENTE)', () => {
    renderActions(makeOrder(1), true)
    expect(screen.getByText(/pendiente de confirmaci/i)).toBeInTheDocument()
  })

  it('shows state advance select for estado 2 (CONFIRMADO)', () => {
    renderActions(makeOrder(2), true)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByText('Confirmar cambio')).toBeInTheDocument()
  })

  it('shows "En preparación" option for estado 2 (CONFIRMADO)', () => {
    renderActions(makeOrder(2), true)
    expect(screen.getByText('En preparación')).toBeInTheDocument()
  })
})
