/**
 * Input component tests.
 *
 * Tests:
 *   - Renders with label (label element linked via htmlFor)
 *   - Error message renders + aria-invalid set + role="alert"
 *   - type="password" is passed through
 *   - Renders without label (no <label> element)
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Input } from '../Input'

describe('Input', () => {
  it('renders visible label associated with input', () => {
    render(<Input id="email" label="Correo electrónico" />)
    const label = screen.getByText('Correo electrónico')
    const input = screen.getByRole('textbox')
    expect(label).toBeInTheDocument()
    expect(input).toHaveAttribute('id', 'email')
    expect(label).toHaveAttribute('for', 'email')
  })

  it('shows error message and sets aria-invalid', () => {
    render(<Input id="email" label="Email" error="El email es requerido" />)
    const input = screen.getByRole('textbox')
    expect(input).toHaveAttribute('aria-invalid', 'true')

    const errorMsg = screen.getByRole('alert')
    expect(errorMsg).toHaveTextContent('El email es requerido')
  })

  it('does not show error markup when error is undefined', () => {
    render(<Input id="name" label="Nombre" />)
    const input = screen.getByRole('textbox')
    expect(input).not.toHaveAttribute('aria-invalid')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('renders password input', () => {
    render(<Input id="password" label="Contraseña" type="password" />)
    // Password inputs don't have role="textbox", query by label
    const input = screen.getByLabelText('Contraseña')
    expect(input).toHaveAttribute('type', 'password')
  })

  it('renders without label', () => {
    render(<Input id="search" placeholder="Buscar..." />)
    expect(screen.queryByRole('label')).not.toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })
})
