/**
 * Tests for CheckoutValidationModal (tasks 11.4–11.7).
 *
 * 11.5 Renders stock shortage items correctly.
 * 11.6 Hard block shows only "Volver al carrito" (no "Continuar").
 * 11.7 Soft warning shows both buttons.
 *
 * The native <dialog> element's showModal()/close() are not supported by jsdom.
 * We patch them before each test (same pattern as Modal.test.tsx).
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CheckoutValidationModal } from '../components/CheckoutValidationModal'
import type { ValidarCarritoResponse } from '../types'

// ---------------------------------------------------------------------------
// jsdom dialog polyfill
// ---------------------------------------------------------------------------

beforeEach(() => {
  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function () {
      this.setAttribute('open', '')
    }
  }
  if (!HTMLDialogElement.prototype.close) {
    HTMLDialogElement.prototype.close = function () {
      this.removeAttribute('open')
      this.dispatchEvent(new Event('close'))
    }
  }
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const CLEAN_RESULT: ValidarCarritoResponse = {
  stock_insuficiente: [],
  productos_invalidos: [],
  cambios_de_precio: [],
  carrito_vacio: false,
  sin_direccion: false,
}

function renderModal(
  validationResult: ValidarCarritoResponse,
  overrides?: Partial<Parameters<typeof CheckoutValidationModal>[0]>,
) {
  return render(
    <CheckoutValidationModal
      isOpen={true}
      onClose={vi.fn()}
      onConfirm={vi.fn()}
      validationResult={validationResult}
      {...overrides}
    />,
  )
}

// ---------------------------------------------------------------------------
// 11.5 — Stock shortage rendered correctly
// ---------------------------------------------------------------------------

describe('CheckoutValidationModal — stock shortage display', () => {
  it('renders stock shortage product name, stock, and requested quantity', () => {
    const result: ValidarCarritoResponse = {
      ...CLEAN_RESULT,
      stock_insuficiente: [
        {
          producto_id: 1,
          nombre: 'Hamburguesa Clásica',
          stock_actual: 2,
          cantidad_solicitada: 5,
        },
      ],
    }

    renderModal(result)

    // Product name visible
    expect(screen.getByText('Hamburguesa Clásica')).toBeInTheDocument()
    // Stock actual
    expect(screen.getByText(/Stock: 2/)).toBeInTheDocument()
    // Cantidad solicitada
    expect(screen.getByText(/Pedido: 5/)).toBeInTheDocument()
  })

  it('renders multiple stock shortage items', () => {
    const result: ValidarCarritoResponse = {
      ...CLEAN_RESULT,
      stock_insuficiente: [
        { producto_id: 1, nombre: 'Pizza', stock_actual: 1, cantidad_solicitada: 3 },
        { producto_id: 2, nombre: 'Pasta', stock_actual: 0, cantidad_solicitada: 2 },
      ],
    }

    renderModal(result)

    expect(screen.getByText('Pizza')).toBeInTheDocument()
    expect(screen.getByText('Pasta')).toBeInTheDocument()
    expect(screen.getByText(/Stock: 1/)).toBeInTheDocument()
    expect(screen.getByText(/Stock: 0/)).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// 11.6 — Hard block: only "Volver al carrito", no "Continuar"
// ---------------------------------------------------------------------------

describe('CheckoutValidationModal — hard block', () => {
  it('shows only "Volver al carrito" when carritoVacio=true', () => {
    renderModal({ ...CLEAN_RESULT, carrito_vacio: true })

    expect(screen.getByRole('button', { name: /volver al carrito/i })).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /continuar/i }),
    ).not.toBeInTheDocument()
  })

  it('shows only "Volver al carrito" when sinDireccion=true', () => {
    renderModal({ ...CLEAN_RESULT, sin_direccion: true })

    expect(screen.getByRole('button', { name: /volver al carrito/i })).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /continuar/i }),
    ).not.toBeInTheDocument()
  })

  it('shows only "Volver al carrito" when productosInvalidos is non-empty', () => {
    renderModal({ ...CLEAN_RESULT, productos_invalidos: [5, 7] })

    expect(screen.getByRole('button', { name: /volver al carrito/i })).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /continuar/i }),
    ).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// 11.7 — Soft warning: both buttons present
// ---------------------------------------------------------------------------

describe('CheckoutValidationModal — soft warning', () => {
  it('shows both buttons when only stock_insuficiente is present', () => {
    const result: ValidarCarritoResponse = {
      ...CLEAN_RESULT,
      stock_insuficiente: [
        { producto_id: 1, nombre: 'Producto', stock_actual: 1, cantidad_solicitada: 3 },
      ],
    }

    renderModal(result)

    expect(screen.getByRole('button', { name: /volver al carrito/i })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /continuar de todas formas/i }),
    ).toBeInTheDocument()
  })

  it('shows both buttons when only cambios_de_precio is present', () => {
    const result: ValidarCarritoResponse = {
      ...CLEAN_RESULT,
      cambios_de_precio: [
        { producto_id: 1, precio_carrito: 100, precio_actual: 120 },
      ],
    }

    renderModal(result)

    expect(screen.getByRole('button', { name: /volver al carrito/i })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /continuar de todas formas/i }),
    ).toBeInTheDocument()
  })

  it('calls onConfirm when "Continuar" is clicked', async () => {
    const onConfirm = vi.fn()
    const onClose = vi.fn()

    const result: ValidarCarritoResponse = {
      ...CLEAN_RESULT,
      stock_insuficiente: [
        { producto_id: 1, nombre: 'P', stock_actual: 1, cantidad_solicitada: 2 },
      ],
    }

    const { getByRole } = render(
      <CheckoutValidationModal
        isOpen={true}
        onClose={onClose}
        onConfirm={onConfirm}
        validationResult={result}
      />,
    )

    getByRole('button', { name: /continuar de todas formas/i }).click()

    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('price changes show before and after values formatted as currency', () => {
    const result: ValidarCarritoResponse = {
      ...CLEAN_RESULT,
      cambios_de_precio: [
        { producto_id: 3, precio_carrito: 99.99, precio_actual: 119.99 },
      ],
    }

    renderModal(result)

    expect(screen.getByText(/\$99\.99/)).toBeInTheDocument()
    expect(screen.getByText(/\$119\.99/)).toBeInTheDocument()
  })
})
