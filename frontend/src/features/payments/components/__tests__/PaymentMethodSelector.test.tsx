/**
 * Tests for PaymentMethodSelector component.
 *
 * Tests:
 *   - Renderización del radiogroup con opciones
 *   - Click en opción habilitada cambia el método en el store
 *   - Click en opción deshabilitada no cambia el método
 *   - Indicador visual de selección correcto
 *   - ARIA attributes correctos
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { PaymentMethodSelector } from '../PaymentMethodSelector'
import { usePaymentStore } from '@/store/paymentStore'

// Reset store state before each test
beforeEach(() => {
  usePaymentStore.getState().reset()
})

describe('PaymentMethodSelector', () => {
  describe('Renderización', () => {
    it('renders the radiogroup with aria-label', () => {
      render(<PaymentMethodSelector />)
      expect(
        screen.getByRole('radiogroup', { name: /método de pago/i }),
      ).toBeInTheDocument()
    })

    it('renders all 3 payment method options', () => {
      render(<PaymentMethodSelector />)
      const radios = screen.getAllByRole('radio')
      expect(radios).toHaveLength(3)
    })

    it('renders MercadoPago option as enabled', () => {
      render(<PaymentMethodSelector />)
      const mp = screen.getByTestId('payment-method-mercadopago')
      expect(mp).toHaveAttribute('aria-disabled', 'false')
    })

    it('renders Tarjeta option as disabled', () => {
      render(<PaymentMethodSelector />)
      const card = screen.getByTestId('payment-method-card')
      expect(card).toHaveAttribute('aria-disabled', 'true')
    })

    it('renders Efectivo option as disabled', () => {
      render(<PaymentMethodSelector />)
      const cash = screen.getByTestId('payment-method-cash')
      expect(cash).toHaveAttribute('aria-disabled', 'true')
    })

    it('all options start with aria-checked false when no method selected', () => {
      render(<PaymentMethodSelector />)
      const radios = screen.getAllByRole('radio')
      radios.forEach((radio) => {
        expect(radio).toHaveAttribute('aria-checked', 'false')
      })
    })
  })

  describe('Selección', () => {
    it('clicking enabled MercadoPago option selects it', () => {
      render(<PaymentMethodSelector />)
      const mp = screen.getByTestId('payment-method-mercadopago')
      fireEvent.click(mp)

      expect(usePaymentStore.getState().method).toBe('mercadopago')
    })

    it('selected option has aria-checked true', () => {
      render(<PaymentMethodSelector />)
      const mp = screen.getByTestId('payment-method-mercadopago')
      fireEvent.click(mp)

      expect(mp).toHaveAttribute('aria-checked', 'true')
    })

    it('clicking disabled Tarjeta option does NOT change method', () => {
      render(<PaymentMethodSelector />)
      const card = screen.getByTestId('payment-method-card')
      fireEvent.click(card)

      expect(usePaymentStore.getState().method).toBeNull()
    })

    it('clicking disabled Efectivo option does NOT change method', () => {
      render(<PaymentMethodSelector />)
      const cash = screen.getByTestId('payment-method-cash')
      fireEvent.click(cash)

      expect(usePaymentStore.getState().method).toBeNull()
    })
  })

  describe('Visual indicator de selección', () => {
    it('shows filled circle indicator when mercadopago is selected', () => {
      usePaymentStore.getState().setMethod('mercadopago')
      render(<PaymentMethodSelector />)

      // The filled dot div should be present (inside the radio indicator)
      const mp = screen.getByTestId('payment-method-mercadopago')
      // The filled indicator is a div with bg-primary inside the radio
      expect(mp.querySelector('.bg-primary')).toBeInTheDocument()
    })

    it('does not show filled circle for unselected option', () => {
      render(<PaymentMethodSelector />)
      const mp = screen.getByTestId('payment-method-mercadopago')
      // No filled dot when not selected
      expect(mp.querySelector('.bg-primary')).not.toBeInTheDocument()
    })
  })
})
