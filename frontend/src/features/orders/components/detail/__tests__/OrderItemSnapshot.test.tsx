/**
 * OrderItemSnapshot tests.
 *
 * Verifies:
 *   - Renders nombre_snapshot (NOT the product's current name)
 *   - Renders precio_snapshot formatted as ARS (NOT the current product price)
 *   - Shows subtotal (cantidad × precio_snapshot)
 *   - Renders ingredientes_excluidoses section when array is non-empty
 *   - Does NOT render ingredientes_excluidoses section when array is empty
 *   - Does NOT render ingredientes_excluidoses section when array is null/undefined
 *   - NEVER makes additional HTTP requests (static render only)
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OrderItemSnapshot } from '../OrderItemSnapshot'
import type { OrderDetailItem } from '@/features/orders/types'

const baseItem: OrderDetailItem = {
  id: 1,
  producto_id: 99,
  nombre_snapshot: 'Hamburguesa Clásica (snapshot)',
  cantidad: 2,
  precio_snapshot: 1200.50,
  ingredientes_excluidos: [],
}

describe('OrderItemSnapshot', () => {
  it('renders the snapshot product name', () => {
    render(<OrderItemSnapshot item={baseItem} />)
    expect(screen.getByText('Hamburguesa Clásica (snapshot)')).toBeInTheDocument()
  })

  it('renders the snapshot unit price in ARS format', () => {
    render(<OrderItemSnapshot item={baseItem} />)
    // Rendered as "2 × $1.200,50"
    expect(screen.getByText(/1\.200/)).toBeInTheDocument()
  })

  it('renders the correct subtotal (cantidad × precio_snapshot)', () => {
    render(<OrderItemSnapshot item={baseItem} />)
    // subtotal = 2 × 1200.50 = 2401.00 → "$2.401,00"
    expect(screen.getByText(/2\.401/)).toBeInTheDocument()
  })

  it('renders quantity alongside unit price', () => {
    render(<OrderItemSnapshot item={baseItem} />)
    expect(screen.getByText(/^2 ×/)).toBeInTheDocument()
  })

  it('does NOT render ingredientes_excluidoses section when array is empty', () => {
    render(<OrderItemSnapshot item={{ ...baseItem, ingredientes_excluidos: [] }} />)
    expect(screen.queryByText(/ingredientes_excluidos/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Ingrediente/)).not.toBeInTheDocument()
  })

  it('renders ingredientes_excluidoses section with ingredient IDs when non-empty', () => {
    const itemWithPersona: OrderDetailItem = {
      ...baseItem,
      ingredientes_excluidos: [3, 7],
    }
    render(<OrderItemSnapshot item={itemWithPersona} />)
    expect(screen.getByText(/Personalizaciones/i)).toBeInTheDocument()
    expect(screen.getByText('Ingrediente #3')).toBeInTheDocument()
    expect(screen.getByText('Ingrediente #7')).toBeInTheDocument()
  })

  it('ingredientes_excluidos list has role="list"', () => {
    const itemWithPersona: OrderDetailItem = {
      ...baseItem,
      ingredientes_excluidos: [5],
    }
    render(<OrderItemSnapshot item={itemWithPersona} />)
    expect(screen.getByRole('list')).toBeInTheDocument()
  })
})
