/**
 * CartItemRow component tests
 *
 * Verifies:
 * - Renders product name, price, quantity
 * - Clicking + on stepper calls onQuantityChange with new value
 * - Clicking remove button calls onRemove with productId
 * - aria-label on article element is correct
 * - When stepper sends 0, onRemove is called (not onQuantityChange)
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { CartItemRow } from '@/features/cart/components/CartItemRow'
import type { CartItem } from '@/store'

const mockItem: CartItem = {
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 10.99,
  quantity: 2,
}

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('CartItemRow', () => {
  it('renders product name and quantity', () => {
    renderWithRouter(
      <CartItemRow
        item={mockItem}
        onQuantityChange={vi.fn()}
        onRemove={vi.fn()}
      />
    )
    expect(screen.getByText('Pepperoni Pizza')).toBeInTheDocument()
    // Input shows the quantity
    const input = screen.getByRole('spinbutton', { name: 'Cantidad' })
    expect(input).toHaveValue(2)
  })

  it('has correct aria-label on the article', () => {
    renderWithRouter(
      <CartItemRow
        item={mockItem}
        onQuantityChange={vi.fn()}
        onRemove={vi.fn()}
      />
    )
    expect(
      screen.getByRole('article', { name: 'Producto: Pepperoni Pizza' })
    ).toBeInTheDocument()
  })

  it('calls onQuantityChange with incremented value when + is clicked', () => {
    const onQuantityChange = vi.fn()
    renderWithRouter(
      <CartItemRow
        item={mockItem}
        onQuantityChange={onQuantityChange}
        onRemove={vi.fn()}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Aumentar cantidad' }))
    expect(onQuantityChange).toHaveBeenCalledWith('pizza-001', 3)
  })

  it('calls onRemove when trash button is clicked', () => {
    const onRemove = vi.fn()
    renderWithRouter(
      <CartItemRow
        item={mockItem}
        onQuantityChange={vi.fn()}
        onRemove={onRemove}
      />
    )
    fireEvent.click(
      screen.getByRole('button', { name: 'Eliminar Pepperoni Pizza del carrito' })
    )
    expect(onRemove).toHaveBeenCalledWith('pizza-001')
  })

  it('calls onRemove (not onQuantityChange) when stepper goes to 0', () => {
    const onQuantityChange = vi.fn()
    const onRemove = vi.fn()
    const itemQty1: CartItem = { ...mockItem, quantity: 1 }
    renderWithRouter(
      <CartItemRow
        item={itemQty1}
        onQuantityChange={onQuantityChange}
        onRemove={onRemove}
      />
    )
    // At quantity=1, the decrement button is the trash icon
    fireEvent.click(
      screen.getByRole('button', { name: 'Eliminar Pepperoni Pizza' })
    )
    expect(onRemove).toHaveBeenCalledWith('pizza-001')
    expect(onQuantityChange).not.toHaveBeenCalled()
  })

  it('renders ingredientes_excluidos as pills', () => {
    const itemWithExclusions: CartItem = {
      ...mockItem,
      ingredientes_excluidos: [3, 7],
    }
    renderWithRouter(
      <CartItemRow
        item={itemWithExclusions}
        onQuantityChange={vi.fn()}
        onRemove={vi.fn()}
      />
    )
    expect(screen.getByText('Sin: #3')).toBeInTheDocument()
    expect(screen.getByText('Sin: #7')).toBeInTheDocument()
  })
})
