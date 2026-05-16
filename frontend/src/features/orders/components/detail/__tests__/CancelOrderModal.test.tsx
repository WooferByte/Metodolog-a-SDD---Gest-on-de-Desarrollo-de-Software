/**
 * CancelOrderModal tests.
 *
 * Verifies:
 *   - Modal content is rendered when isCancelModalOpen is true
 *   - "Sí, cancelar pedido" button is present when modal is open
 *   - "No, mantener pedido" button closes the modal (calls closeCancelModal)
 *   - Order ID appears in the modal description
 *
 * Note: The modal uses the native <dialog> element (showModal() API).
 * jsdom does not implement showModal(), so we mock HTMLDialogElement.prototype.showModal
 * and HTMLDialogElement.prototype.close as no-ops to avoid TypeError in tests.
 *
 * Focus trap, Escape-key behavior, and aria-modal are all native <dialog> features
 * not testable in jsdom — they are verified in the E2E Playwright tests instead.
 */

import '@testing-library/jest-dom'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CancelOrderModal } from '../CancelOrderModal'
import { useOrderDetailStore } from '@/features/orders/store/orderDetailStore'

// Mock native <dialog> methods not implemented in jsdom
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn()
  HTMLDialogElement.prototype.close = vi.fn()
})

function renderModal(orderId: number) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <CancelOrderModal orderId={orderId} />
    </QueryClientProvider>,
  )
}

describe('CancelOrderModal', () => {
  beforeEach(() => {
    // Reset store state before each test
    useOrderDetailStore.setState({
      isCancelModalOpen: false,
    })
  })

  it('renders modal title when isCancelModalOpen is true', () => {
    useOrderDetailStore.setState({ isCancelModalOpen: true })
    renderModal(42)
    expect(screen.getByText('Cancelar pedido')).toBeInTheDocument()
  })

  it('calls showModal() on the dialog element when isCancelModalOpen is true', () => {
    useOrderDetailStore.setState({ isCancelModalOpen: true })
    renderModal(42)
    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalled()
  })

  it('shows the order ID in the description when open', () => {
    useOrderDetailStore.setState({ isCancelModalOpen: true })
    renderModal(42)
    expect(screen.getByText(/#42/)).toBeInTheDocument()
  })

  it('shows "Sí, cancelar pedido" confirm button when open', () => {
    useOrderDetailStore.setState({ isCancelModalOpen: true })
    renderModal(42)
    expect(screen.getByText('Sí, cancelar pedido')).toBeInTheDocument()
  })

  it('shows "No, mantener pedido" cancel button when open', () => {
    useOrderDetailStore.setState({ isCancelModalOpen: true })
    renderModal(42)
    expect(screen.getByText('No, mantener pedido')).toBeInTheDocument()
  })

  it('calls closeCancelModal when "No, mantener pedido" is clicked', () => {
    useOrderDetailStore.setState({ isCancelModalOpen: true })
    renderModal(42)
    fireEvent.click(screen.getByText('No, mantener pedido'))
    expect(useOrderDetailStore.getState().isCancelModalOpen).toBe(false)
  })

  it('confirm button has correct aria-label with order ID', () => {
    useOrderDetailStore.setState({ isCancelModalOpen: true })
    renderModal(42)
    expect(
      screen.getByLabelText('Confirmar cancelación del pedido #42'),
    ).toBeInTheDocument()
  })
})
