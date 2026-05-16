/**
 * OrderTimeline tests.
 *
 * Verifies:
 *   - Renders N items for N entries in historial
 *   - Items are rendered in chronological order (oldest first)
 *   - Shows "Sistema" fallback when usuario_email is null
 *   - Shows the user email when provided
 *   - Shows "Sin historial" message when historial is empty
 *   - Uses role="list" on the timeline container
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OrderTimeline } from '../OrderTimeline'
import type { OrderHistorialItem } from '@/features/orders/types'

const historialItems: OrderHistorialItem[] = [
  {
    id: 1,
    pedido_id: 10,
    estado_anterior_id: null,
    estado_nuevo_id: 1,        // PENDIENTE
    observacion: null,
    usuario_responsable_id: null,
    usuario_email: null,
    creado_en: '2026-05-10T10:00:00Z',
  },
  {
    id: 2,
    pedido_id: 10,
    estado_anterior_id: 1,
    estado_nuevo_id: 2,        // CONFIRMADO
    observacion: null,
    usuario_responsable_id: 1,
    usuario_email: 'admin@foodstore.com',
    creado_en: '2026-05-10T12:00:00Z',
  },
  {
    id: 3,
    pedido_id: 10,
    estado_anterior_id: 2,
    estado_nuevo_id: 3,        // EN_PREPARACIÓN
    observacion: null,
    usuario_responsable_id: 4,
    usuario_email: 'pedidos@test.com',
    creado_en: '2026-05-10T14:00:00Z',
  },
]

describe('OrderTimeline', () => {
  it('renders N list items for N historial entries', () => {
    render(<OrderTimeline historial={historialItems} />)
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(3)
  })

  it('shows "Sistema" fallback when usuario_email is null', () => {
    render(<OrderTimeline historial={historialItems} />)
    expect(screen.getByText('Sistema')).toBeInTheDocument()
  })

  it('shows usuario_email when provided', () => {
    render(<OrderTimeline historial={historialItems} />)
    expect(screen.getByText('admin@foodstore.com')).toBeInTheDocument()
    expect(screen.getByText('pedidos@test.com')).toBeInTheDocument()
  })

  it('renders items in chronological order (oldest first)', () => {
    // Items passed in reverse order — should still render oldest first
    const reversed = [...historialItems].reverse()
    render(<OrderTimeline historial={reversed} />)
    const items = screen.getAllByRole('listitem')
    // First item should have the earliest date (item with estado_nuevo_id=1)
    // The badge label for estado 1 is "Pendiente"
    const firstItem = items[0]
    expect(firstItem).toHaveTextContent('Pendiente')
  })

  it('shows "Sin historial" message when historial is empty', () => {
    render(<OrderTimeline historial={[]} />)
    expect(screen.getByText(/Sin historial/i)).toBeInTheDocument()
  })

  it('has role="list" on the ordered list', () => {
    render(<OrderTimeline historial={historialItems} />)
    expect(screen.getByRole('list')).toBeInTheDocument()
  })
})
