/**
 * OrderStatusBadge tests.
 *
 * Covers:
 *   - Known status IDs (1 PENDIENTE, 5 ENTREGADO, 6 CANCELADO)
 *   - Unknown status ID (99) → fallback "Desconocido"
 *   - aria-label presence for accessibility
 *   - Custom className passthrough
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OrderStatusBadge } from '../OrderStatusBadge'

describe('OrderStatusBadge', () => {
  it('renders PENDIENTE label for statusId=1', () => {
    render(<OrderStatusBadge statusId={1} />)
    expect(screen.getByText('Pendiente')).toBeInTheDocument()
  })

  it('renders ENTREGADO label for statusId=5', () => {
    render(<OrderStatusBadge statusId={5} />)
    expect(screen.getByText('Entregado')).toBeInTheDocument()
  })

  it('renders CANCELADO label for statusId=6', () => {
    render(<OrderStatusBadge statusId={6} />)
    expect(screen.getByText('Cancelado')).toBeInTheDocument()
  })

  it('renders fallback "Desconocido" for unknown statusId=99', () => {
    render(<OrderStatusBadge statusId={99} />)
    expect(screen.getByText('Desconocido')).toBeInTheDocument()
  })

  it('has aria-label describing the status', () => {
    render(<OrderStatusBadge statusId={2} />)
    const badge = screen.getByLabelText('Estado del pedido: Confirmado')
    expect(badge).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<OrderStatusBadge statusId={1} className="extra-class" />)
    const badge = screen.getByText('Pendiente')
    expect(badge.className).toContain('extra-class')
  })
})
