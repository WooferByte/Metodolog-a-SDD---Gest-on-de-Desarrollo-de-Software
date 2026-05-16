/**
 * OrdersSkeleton tests.
 *
 * Covers:
 *   - mode="client": renders correct number of card skeletons
 *   - mode="admin": renders correct number of row skeletons
 *   - aria-busy and aria-label presence
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OrdersSkeleton } from '../OrdersSkeleton'

describe('OrdersSkeleton — mode client', () => {
  it('renders N card skeletons with aria-label', () => {
    render(<OrdersSkeleton mode="client" count={3} />)
    const items = screen.getAllByLabelText('Cargando pedido...')
    expect(items).toHaveLength(3)
  })

  it('renders 5 skeletons by default', () => {
    render(<OrdersSkeleton mode="client" />)
    const items = screen.getAllByLabelText('Cargando pedido...')
    expect(items).toHaveLength(5)
  })

  it('container has aria-busy=true attribute', () => {
    const { container } = render(<OrdersSkeleton mode="client" count={2} />)
    // The outermost div wrapping the grid should have aria-busy=true
    const grid = container.querySelector('[aria-busy="true"]')
    expect(grid).not.toBeNull()
  })
})

describe('OrdersSkeleton — mode admin', () => {
  it('renders N row skeletons', () => {
    // mode=admin renders <tr> elements — need table wrapper for valid HTML
    render(
      <table>
        <tbody>
          <OrdersSkeleton mode="admin" count={4} />
        </tbody>
      </table>,
    )
    const rows = screen.getAllByLabelText('Cargando fila...')
    expect(rows).toHaveLength(4)
  })

  it('renders 5 rows by default', () => {
    render(
      <table>
        <tbody>
          <OrdersSkeleton mode="admin" />
        </tbody>
      </table>,
    )
    const rows = screen.getAllByLabelText('Cargando fila...')
    expect(rows).toHaveLength(5)
  })
})
