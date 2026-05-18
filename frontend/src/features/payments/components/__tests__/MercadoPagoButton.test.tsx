/**
 * Tests for MercadoPagoButton component.
 *
 * Tests:
 *   - SDK not available: renders error message, button disabled
 *   - SDK available, no preferenceId: button disabled
 *   - SDK available, preferenceId set: button enabled
 *   - Loading states: aria-busy, disabled, spinner text
 *   - Click calls mp.checkout() with correct preferenceId
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MercadoPagoButton } from '../MercadoPagoButton'
import { usePaymentStore } from '@/store/paymentStore'

// Reset store and window.MercadoPago before each test
beforeEach(() => {
  usePaymentStore.getState().reset()
  usePaymentStore.getState().setMethod('mercadopago')
  // Clean up any existing window.MercadoPago
  delete (window as typeof window & { MercadoPago?: unknown }).MercadoPago
})

afterEach(() => {
  delete (window as typeof window & { MercadoPago?: unknown }).MercadoPago
  vi.restoreAllMocks()
})

describe('MercadoPagoButton', () => {
  describe('SDK no disponible', () => {
    it('shows error message when window.MercadoPago is not defined', () => {
      // SDK not loaded
      render(<MercadoPagoButton />)
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(
        screen.getByText(/procesador de pagos no está disponible/i),
      ).toBeInTheDocument()
    })

    it('does not render the payment button when SDK is missing', () => {
      render(<MercadoPagoButton />)
      expect(
        screen.queryByTestId('mercadopago-button'),
      ).not.toBeInTheDocument()
    })
  })

  describe('SDK disponible', () => {
    beforeEach(() => {
      // Mock window.MercadoPago constructor
      const mockCheckout = vi.fn()
      window.MercadoPago = vi.fn().mockImplementation(() => ({
        checkout: mockCheckout,
      }))
    })

    it('renders the payment button when SDK is available', () => {
      render(<MercadoPagoButton />)
      expect(screen.getByTestId('mercadopago-button')).toBeInTheDocument()
    })

    it('button is disabled when preferenceId is null', () => {
      render(<MercadoPagoButton />)
      const btn = screen.getByTestId('mercadopago-button')
      expect(btn).toBeDisabled()
      expect(btn).toHaveAttribute('aria-disabled', 'true')
    })

    it('button is enabled when preferenceId is set', () => {
      usePaymentStore.getState().setPreference('pref-123', 1, 'https://mp.com')
      usePaymentStore.getState().setStatus('idle')
      render(<MercadoPagoButton />)
      const btn = screen.getByTestId('mercadopago-button')
      expect(btn).not.toBeDisabled()
      expect(btn).toHaveAttribute('aria-disabled', 'false')
    })

    it('shows "Pagar con MercadoPago" label when idle with preferenceId', () => {
      usePaymentStore.getState().setPreference('pref-123', 1, 'https://mp.com')
      render(<MercadoPagoButton />)
      expect(screen.getByText('Pagar con MercadoPago')).toBeInTheDocument()
    })
  })

  describe('Estados de carga', () => {
    beforeEach(() => {
      window.MercadoPago = vi.fn().mockImplementation(() => ({
        checkout: vi.fn(),
      }))
    })

    it('shows "Creando pedido..." when status is creating_order', () => {
      usePaymentStore.getState().setStatus('creating_order')
      render(<MercadoPagoButton />)
      expect(screen.getByText('Creando pedido...')).toBeInTheDocument()
    })

    it('shows "Generando pago..." when status is creating_preference', () => {
      usePaymentStore.getState().setStatus('creating_preference')
      render(<MercadoPagoButton />)
      expect(screen.getByText('Generando pago...')).toBeInTheDocument()
    })

    it('has aria-busy=true when loading', () => {
      usePaymentStore.getState().setStatus('creating_order')
      render(<MercadoPagoButton />)
      expect(screen.getByTestId('mercadopago-button')).toHaveAttribute(
        'aria-busy',
        'true',
      )
    })
  })

  describe('Llamada al SDK', () => {
    it('calls mp.checkout() with correct preferenceId on click', async () => {
      const mockCheckout = vi.fn()
      window.MercadoPago = vi.fn().mockImplementation(() => ({
        checkout: mockCheckout,
      }))

      usePaymentStore.getState().setPreference('pref-abc-123', 1, 'https://mp.com')
      usePaymentStore.getState().setStatus('idle')

      render(<MercadoPagoButton />)

      // Wait for useEffect to run and enable the button
      await waitFor(() => {
        const btn = screen.getByTestId('mercadopago-button')
        expect(btn).not.toBeDisabled()
      })

      fireEvent.click(screen.getByTestId('mercadopago-button'))

      expect(mockCheckout).toHaveBeenCalledWith({
        preference: { id: 'pref-abc-123' },
        autoOpen: true,
      })
    })

    it('sets status to waiting_payment after clicking', async () => {
      const mockCheckout = vi.fn()
      window.MercadoPago = vi.fn().mockImplementation(() => ({
        checkout: mockCheckout,
      }))

      usePaymentStore.getState().setPreference('pref-xyz', 2, 'https://mp.com')
      usePaymentStore.getState().setStatus('idle')

      render(<MercadoPagoButton />)

      // Wait for useEffect to set sdkAvailable=true
      await waitFor(() => {
        expect(screen.getByTestId('mercadopago-button')).not.toBeDisabled()
      })

      fireEvent.click(screen.getByTestId('mercadopago-button'))

      expect(usePaymentStore.getState().status).toBe('waiting_payment')
    })
  })
})
