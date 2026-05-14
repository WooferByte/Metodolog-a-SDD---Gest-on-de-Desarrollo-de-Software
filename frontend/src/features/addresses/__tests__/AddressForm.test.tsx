/**
 * AddressForm component tests.
 *
 * Tests:
 *   - Renders all fields
 *   - Pre-fills fields when initialData is provided (edit mode)
 *   - Fields are empty when no initialData (create mode)
 *   - Shows validation error when alias is empty and form is submitted
 *   - Calls onSubmit with correct data when validation passes
 *   - Submit button is disabled when isLoading === true
 *   - Calls onCancel when "Cancelar" is clicked
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AddressForm } from '@/features/addresses/components/AddressForm'
import type { DireccionCreate, DireccionResponse } from '@/features/addresses/types'

// ── Fixture ───────────────────────────────────────────────────────────────────

const mockAddress: DireccionResponse = {
  id: 1,
  usuario_id: 2,
  alias: 'Casa',
  linea1: 'Av. Corrientes 1234',
  piso: '3',
  departamento: 'A',
  ciudad: 'Buenos Aires',
  codigo_postal: '1043',
  referencia: 'Timbre A',
  es_predeterminada: true,
  creado_en: '2024-01-01T00:00:00',
  actualizado_en: '2024-01-01T00:00:00',
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('AddressForm', () => {
  const onSubmit = vi.fn()
  const onCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all expected fields', () => {
    render(<AddressForm onSubmit={onSubmit} onCancel={onCancel} />)

    expect(screen.getByLabelText(/alias/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/dirección/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/ciudad/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/código postal/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/piso/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/departamento/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/referencia/i)).toBeInTheDocument()
  })

  it('pre-fills fields when initialData is provided (edit mode)', () => {
    render(<AddressForm initialData={mockAddress} onSubmit={onSubmit} onCancel={onCancel} />)

    expect(screen.getByLabelText(/alias/i)).toHaveValue('Casa')
    expect(screen.getByLabelText(/dirección/i)).toHaveValue('Av. Corrientes 1234')
    expect(screen.getByLabelText(/ciudad/i)).toHaveValue('Buenos Aires')
    expect(screen.getByLabelText(/código postal/i)).toHaveValue('1043')
    expect(screen.getByLabelText(/piso/i)).toHaveValue('3')
    expect(screen.getByLabelText(/departamento/i)).toHaveValue('A')
    expect(screen.getByLabelText(/referencia/i)).toHaveValue('Timbre A')
  })

  it('fields are empty when no initialData (create mode)', () => {
    render(<AddressForm onSubmit={onSubmit} onCancel={onCancel} />)

    expect(screen.getByLabelText(/alias/i)).toHaveValue('')
    expect(screen.getByLabelText(/dirección/i)).toHaveValue('')
    expect(screen.getByLabelText(/ciudad/i)).toHaveValue('')
    expect(screen.getByLabelText(/código postal/i)).toHaveValue('')
  })

  it('shows validation error when alias is empty on submit', () => {
    render(<AddressForm onSubmit={onSubmit} onCancel={onCancel} />)

    // Fill required fields except alias
    fireEvent.change(screen.getByLabelText(/dirección/i), {
      target: { value: 'Av. Corrientes 1234' },
    })
    fireEvent.change(screen.getByLabelText(/ciudad/i), {
      target: { value: 'Buenos Aires' },
    })
    fireEvent.change(screen.getByLabelText(/código postal/i), {
      target: { value: '1043' },
    })

    fireEvent.click(screen.getByRole('button', { name: /guardar/i }))

    expect(screen.getByText(/alias es requerido/i)).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit with correct data when validation passes', () => {
    render(<AddressForm onSubmit={onSubmit} onCancel={onCancel} />)

    fireEvent.change(screen.getByLabelText(/alias/i), { target: { value: 'Casa' } })
    fireEvent.change(screen.getByLabelText(/dirección/i), {
      target: { value: 'Av. Corrientes 1234' },
    })
    fireEvent.change(screen.getByLabelText(/ciudad/i), {
      target: { value: 'Buenos Aires' },
    })
    fireEvent.change(screen.getByLabelText(/código postal/i), {
      target: { value: '1043' },
    })

    fireEvent.click(screen.getByRole('button', { name: /guardar/i }))

    const expectedPayload: DireccionCreate = {
      alias: 'Casa',
      linea1: 'Av. Corrientes 1234',
      ciudad: 'Buenos Aires',
      codigo_postal: '1043',
    }

    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(onSubmit).toHaveBeenCalledWith(expectedPayload)
  })

  it('submit button is disabled when isLoading is true', () => {
    render(<AddressForm onSubmit={onSubmit} onCancel={onCancel} isLoading />)

    expect(screen.getByRole('button', { name: /guardar/i })).toBeDisabled()
  })

  it('calls onCancel when "Cancelar" is clicked', () => {
    render(<AddressForm onSubmit={onSubmit} onCancel={onCancel} />)

    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  it('shows "Actualizar" button in edit mode', () => {
    render(<AddressForm initialData={mockAddress} onSubmit={onSubmit} onCancel={onCancel} />)

    expect(screen.getByRole('button', { name: /actualizar/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^guardar$/i })).not.toBeInTheDocument()
  })
})
