/**
 * QuantityStepper component tests
 *
 * Verifies:
 * - Renders current value
 * - + button calls onChange with value+1
 * - - button at value>min calls onChange with value-1
 * - - button at value=min (trash state) calls onChange(0)
 * - ARIA attributes present
 * - + button disabled when at max
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QuantityStepper } from '@/features/cart/components/QuantityStepper'

describe('QuantityStepper', () => {
  it('renders the current quantity value', () => {
    render(
      <QuantityStepper
        value={3}
        onChange={vi.fn()}
        productName="Pizza"
      />
    )
    const input = screen.getByRole('spinbutton', { name: 'Cantidad' })
    expect(input).toHaveValue(3)
  })

  it('calls onChange(value+1) when + is clicked', () => {
    const onChange = vi.fn()
    render(
      <QuantityStepper
        value={2}
        onChange={onChange}
        productName="Calzone"
      />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Aumentar cantidad' }))
    expect(onChange).toHaveBeenCalledWith(3)
  })

  it('calls onChange(value-1) when - is clicked at value > min', () => {
    const onChange = vi.fn()
    render(
      <QuantityStepper
        value={3}
        onChange={onChange}
        productName="Calzone"
      />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Disminuir cantidad' }))
    expect(onChange).toHaveBeenCalledWith(2)
  })

  it('calls onChange(0) when at min value (trash state) — parent removes item', () => {
    const onChange = vi.fn()
    render(
      <QuantityStepper
        value={1}
        min={1}
        onChange={onChange}
        productName="Pizza"
      />
    )
    // At min, button label changes to "Eliminar {productName}"
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar Pizza' }))
    expect(onChange).toHaveBeenCalledWith(0)
  })

  it('has role="group" with aria-label for the product', () => {
    render(
      <QuantityStepper
        value={2}
        onChange={vi.fn()}
        productName="Empanada"
      />
    )
    expect(screen.getByRole('group', { name: 'Cantidad de Empanada' })).toBeInTheDocument()
  })

  it('+ button is disabled when at max', () => {
    render(
      <QuantityStepper
        value={99}
        max={99}
        onChange={vi.fn()}
        productName="Pizza"
      />
    )
    expect(screen.getByRole('button', { name: 'Aumentar cantidad' })).toBeDisabled()
  })
})
