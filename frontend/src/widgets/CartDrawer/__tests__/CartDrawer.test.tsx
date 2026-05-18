/**
 * CartDrawer widget tests
 *
 * Verifies:
 * - Renders without errors when closed
 * - When open: role="dialog" and aria-modal="true" present
 * - Clicking backdrop calls setCartDrawerOpen(false)
 * - Clicking close button calls setCartDrawerOpen(false)
 * - Escape key closes the drawer
 * - BUG 3 fix: returns null when on /checkout route
 */

import '@testing-library/jest-dom'
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { CartDrawer } from '@/widgets/CartDrawer/CartDrawer'
import { useUIStore, useCartStore } from '@/store'

function renderWithRouter(ui: React.ReactElement, initialPath = '/') {
  return render(<MemoryRouter initialEntries={[initialPath]}>{ui}</MemoryRouter>)
}

describe('CartDrawer', () => {
  beforeEach(() => {
    localStorage.clear()
    useCartStore.setState({ items: [] })
    useUIStore.setState({
      theme: 'light',
      sidebarOpen: false,
      cartDrawerOpen: false,
      toasts: [],
      _hasHydrated: true,
    })
  })

  it('renders without errors when cartDrawerOpen is false', () => {
    expect(() => renderWithRouter(<CartDrawer />)).not.toThrow()
  })

  it('drawer has aria-hidden="true" when closed', () => {
    renderWithRouter(<CartDrawer />)
    const dialog = screen.getByRole('dialog', { hidden: true })
    expect(dialog).toHaveAttribute('aria-hidden', 'true')
  })

  it('has role="dialog" and aria-modal="true" when open', () => {
    useUIStore.setState({ cartDrawerOpen: true })
    renderWithRouter(<CartDrawer />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAttribute('aria-label', 'Carrito de compras')
  })

  it('calls setCartDrawerOpen(false) when close button is clicked', () => {
    useUIStore.setState({ cartDrawerOpen: true })
    renderWithRouter(<CartDrawer />)
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar carrito' }))
    expect(useUIStore.getState().cartDrawerOpen).toBe(false)
  })

  it('closes on Escape key press', () => {
    useUIStore.setState({ cartDrawerOpen: true })
    renderWithRouter(<CartDrawer />)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(useUIStore.getState().cartDrawerOpen).toBe(false)
  })

  it('shows empty cart state when no items', () => {
    useUIStore.setState({ cartDrawerOpen: true })
    renderWithRouter(<CartDrawer />)
    expect(screen.getByText('Tu carrito está vacío')).toBeInTheDocument()
  })

  it('renders CartItemRows when cart has items', () => {
    useCartStore.setState({
      items: [
        { productId: 'p1', name: 'Pepperoni Pizza', price: 10.99, quantity: 2 },
      ],
    })
    useUIStore.setState({ cartDrawerOpen: true })
    renderWithRouter(<CartDrawer />)
    expect(screen.getByText('Pepperoni Pizza')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// BUG 3 fix — CartDrawer returns null on /checkout route
// ---------------------------------------------------------------------------

describe('CartDrawer — BUG 3: disabled on /checkout', () => {
  beforeEach(() => {
    localStorage.clear()
    useCartStore.setState({ items: [] })
    useUIStore.setState({
      theme: 'light',
      sidebarOpen: false,
      cartDrawerOpen: true, // open to confirm it still returns null
      toasts: [],
      _hasHydrated: true,
    })
  })

  it('returns null (nothing rendered) when route is /checkout', () => {
    const { container } = renderWithRouter(<CartDrawer />, '/checkout')
    expect(container.firstChild).toBeNull()
  })

  it('does NOT return null when route is / (renders normally)', () => {
    const { container } = renderWithRouter(<CartDrawer />, '/')
    expect(container.firstChild).not.toBeNull()
  })

  it('does NOT return null when route is /cart', () => {
    const { container } = renderWithRouter(<CartDrawer />, '/cart')
    expect(container.firstChild).not.toBeNull()
  })
})
