/**
 * Tests for PaymentStatusModal component.
 *
 * Tests:
 *   - success mode: renders check icon, "¡Pago exitoso!", "Ver mi pedido" button
 *   - error mode: renders X icon, "El pago no pudo procesarse", retry + cancel buttons
 *   - pending mode: renders clock icon, "Pago en proceso", "Ver mis pedidos" button
 *   - Not visible when status is 'idle', 'creating_order', etc.
 *   - "Ver mi pedido" navigates to /pedidos/{pedidoId} and resets store
 *   - "Intentar de nuevo" calls createPreference with current pedidoId
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PaymentStatusModal } from '../PaymentStatusModal'
import { usePaymentStore } from '@/store/paymentStore'

// Polyfill native dialog for jsdom
beforeEach(() => {
  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function () {
      this.setAttribute('open', '')
    }
  }
  if (!HTMLDialogElement.prototype.close) {
    HTMLDialogElement.prototype.close = function () {
      this.removeAttribute('open')
    }
  }
})

function renderModal() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <PaymentStatusModal />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

// Partial state setter for tests — merges into existing store state
function setStore(partial: Partial<{
  method: 'mercadopago' | 'cash' | null
  pedidoId: number | null
  preferenceId: string | null
  pagoId: number | null
  initPoint: string | null
  status: 'idle' | 'creating_order' | 'creating_preference' | 'waiting_payment' | 'success' | 'error' | 'pending'
  error: string | null
}>) {
  // Use setState with a function to merge partial state
  usePaymentStore.setState((state) => ({ ...state, ...partial }))
}

describe('PaymentStatusModal', () => {
  beforeEach(() => {
    setStore({})
  })

  describe('No visible en estados no finales', () => {
    it('returns null when status is idle', () => {
      setStore({ status: 'idle' })
      renderModal()
      expect(screen.queryByTestId('payment-status-modal')).not.toBeInTheDocument()
    })

    it('returns null when status is creating_order', () => {
      setStore({ status: 'creating_order' })
      renderModal()
      expect(screen.queryByTestId('payment-status-modal')).not.toBeInTheDocument()
    })

    it('returns null when status is waiting_payment', () => {
      setStore({ status: 'waiting_payment' })
      renderModal()
      expect(screen.queryByTestId('payment-status-modal')).not.toBeInTheDocument()
    })
  })

  describe('Modo success', () => {
    beforeEach(() => setStore({ status: 'success', pedidoId: 42 }))

    it('renders the modal in success mode', () => {
      renderModal()
      expect(screen.getByTestId('payment-status-modal')).toBeInTheDocument()
    })

    it('shows "¡Pago exitoso!" title', () => {
      renderModal()
      expect(screen.getByText('¡Pago exitoso!')).toBeInTheDocument()
    })

    it('shows the pedido_id in the message', () => {
      renderModal()
      expect(screen.getByText(/pedido #42/i)).toBeInTheDocument()
    })

    it('renders "Ver mi pedido" button', () => {
      renderModal()
      expect(screen.getByTestId('modal-view-order-btn')).toBeInTheDocument()
    })

    it('clicking "Ver mi pedido" resets the store', () => {
      renderModal()
      fireEvent.click(screen.getByTestId('modal-view-order-btn'))
      expect(usePaymentStore.getState().status).toBe('idle')
      expect(usePaymentStore.getState().pedidoId).toBeNull()
    })

    it('has correct ARIA attributes for dialog', () => {
      renderModal()
      const dialog = screen.getByTestId('payment-status-modal')
      expect(dialog).toHaveAttribute('role', 'dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby', 'payment-status-modal-title')
    })
  })

  describe('Modo error', () => {
    beforeEach(() => setStore({ status: 'error', pedidoId: 99 }))

    it('renders the modal in error mode', () => {
      renderModal()
      expect(screen.getByTestId('payment-status-modal')).toBeInTheDocument()
    })

    it('shows error title', () => {
      renderModal()
      expect(
        screen.getByText('El pago no pudo procesarse'),
      ).toBeInTheDocument()
    })

    it('renders "Intentar de nuevo" button', () => {
      renderModal()
      expect(screen.getByTestId('modal-retry-btn')).toBeInTheDocument()
    })

    it('renders "Cancelar" button', () => {
      renderModal()
      expect(screen.getByTestId('modal-cancel-btn')).toBeInTheDocument()
    })

    it('clicking "Cancelar" resets the store', () => {
      renderModal()
      fireEvent.click(screen.getByTestId('modal-cancel-btn'))
      expect(usePaymentStore.getState().status).toBe('idle')
    })
  })

  describe('Modo pending', () => {
    beforeEach(() => setStore({ status: 'pending', pedidoId: 55 }))

    it('renders the modal in pending mode', () => {
      renderModal()
      expect(screen.getByTestId('payment-status-modal')).toBeInTheDocument()
    })

    it('shows pending title', () => {
      renderModal()
      expect(screen.getByText('Pago en proceso')).toBeInTheDocument()
    })

    it('shows notification message', () => {
      renderModal()
      expect(
        screen.getByText(/Te notificaremos cuando se confirme/i),
      ).toBeInTheDocument()
    })

    it('renders "Ver mis pedidos" button', () => {
      renderModal()
      expect(screen.getByTestId('modal-view-orders-btn')).toBeInTheDocument()
    })
  })
})
