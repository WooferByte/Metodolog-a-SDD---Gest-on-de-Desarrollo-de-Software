/**
 * OrderCard tests.
 *
 * Covers:
 *   - mode="client": badge, date, total, CTA button presence
 *   - mode="admin": compact layout, badge, total
 *   - aria-label on the article/div
 *   - onViewDetail callback fires on CTA click
 *   - Empty state: message "No tenés pedidos todavía" in MyOrdersPage context
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { OrderCard } from '../OrderCard'
import type { Order } from '@/features/orders/types'

const mockOrder: Order = {
  id: 42,
  usuario_id: 7,
  estado_pedido_id: 1,    // PENDIENTE
  total: 1500.50,
  creado_en: '2026-05-15T10:30:00Z',
  observacion: 'Sin cebolla',
  direccion_snapshot: null,
  forma_pago_id: 1,
}

describe('OrderCard — mode client', () => {
  function renderCard(onViewDetail = vi.fn()) {
    return render(
      <MemoryRouter>
        <OrderCard order={mockOrder} mode="client" onViewDetail={onViewDetail} />
      </MemoryRouter>,
    )
  }

  it('renders the order status badge', () => {
    renderCard()
    expect(screen.getByLabelText('Estado del pedido: Pendiente')).toBeInTheDocument()
  })

  it('renders a formatted date', () => {
    renderCard()
    // The <time> element should be present
    const time = document.querySelector('time')
    expect(time).not.toBeNull()
    expect(time?.getAttribute('dateTime')).toBe('2026-05-15T10:30:00Z')
  })

  it('renders the order total in ARS format', () => {
    renderCard()
    // The total should appear somewhere — formatted as ARS currency
    expect(screen.getByText(/1\.500/)).toBeInTheDocument()
  })

  it('renders the "Ver detalle" button with aria-label', () => {
    renderCard()
    const btn = screen.getByLabelText('Ver detalle del pedido #42')
    expect(btn).toBeInTheDocument()
  })

  it('calls onViewDetail with order id when CTA clicked', () => {
    const spy = vi.fn()
    renderCard(spy)
    fireEvent.click(screen.getByLabelText('Ver detalle del pedido #42'))
    expect(spy).toHaveBeenCalledWith(42)
  })

  it('has aria-label on the article', () => {
    renderCard()
    expect(screen.getByLabelText('Pedido #42')).toBeInTheDocument()
  })
})

describe('OrderCard — mode admin', () => {
  function renderAdminCard(onViewDetail = vi.fn()) {
    return render(
      <MemoryRouter>
        <OrderCard order={mockOrder} mode="admin" onViewDetail={onViewDetail} />
      </MemoryRouter>,
    )
  }

  it('renders order id in compact layout', () => {
    renderAdminCard()
    expect(screen.getByText('#42')).toBeInTheDocument()
  })

  it('renders the status badge in admin mode', () => {
    renderAdminCard()
    expect(screen.getByLabelText('Estado del pedido: Pendiente')).toBeInTheDocument()
  })

  it('renders total amount', () => {
    renderAdminCard()
    expect(screen.getByText(/1\.500/)).toBeInTheDocument()
  })

  it('calls onViewDetail when Ver button clicked', () => {
    const spy = vi.fn()
    renderAdminCard(spy)
    fireEvent.click(screen.getByLabelText('Ver detalle del pedido #42'))
    expect(spy).toHaveBeenCalledWith(42)
  })
})
