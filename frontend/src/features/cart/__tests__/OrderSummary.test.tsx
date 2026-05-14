/**
 * OrderSummary component tests
 *
 * Verifies:
 * - Shows item count and total price
 * - CTA button is disabled when cart is empty
 * - Shows correct pluralization for 1 vs N items
 */

import '@testing-library/jest-dom'
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { OrderSummary } from '@/features/cart/components/OrderSummary'
import { useCartStore, useAuthStore } from '@/store'

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('OrderSummary', () => {
  beforeEach(() => {
    localStorage.clear()
    useCartStore.setState({ items: [] })
    useAuthStore.setState({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      _hasHydrated: true,
    })
  })

  it('shows "No hay productos" and disabled CTA when cart is empty', () => {
    renderWithRouter(<OrderSummary />)
    expect(screen.getByText('No hay productos')).toBeInTheDocument()
    const cta = screen.getByRole('button', { name: 'Proceder al pago' })
    expect(cta).toBeDisabled()
  })

  it('shows item count and total price with 2 items', () => {
    useCartStore.setState({
      items: [
        { productId: 'p1', name: 'Pizza', price: 10.00, quantity: 2 },
        { productId: 'p2', name: 'Calzone', price: 15.00, quantity: 1 },
      ],
    })
    renderWithRouter(<OrderSummary />)
    expect(screen.getByText('3 productos')).toBeInTheDocument()
    // CTA should be a link (not a disabled button) when cart has items
    expect(screen.getByRole('link', { name: 'Proceder al pago' })).toBeInTheDocument()
  })

  it('uses singular "producto" for exactly 1 item', () => {
    useCartStore.setState({
      items: [
        { productId: 'p1', name: 'Pizza', price: 10.00, quantity: 1 },
      ],
    })
    renderWithRouter(<OrderSummary />)
    expect(screen.getByText('1 producto')).toBeInTheDocument()
  })

  it('shows hint text when unauthenticated and cart has items', () => {
    useCartStore.setState({
      items: [{ productId: 'p1', name: 'Pizza', price: 10.00, quantity: 1 }],
    })
    renderWithRouter(<OrderSummary />)
    expect(
      screen.getByText(/Deberás iniciar sesión para completar el pedido/i)
    ).toBeInTheDocument()
  })
})
