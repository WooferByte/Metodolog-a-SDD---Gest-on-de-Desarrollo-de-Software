/**
 * AddressCard component tests.
 *
 * Tests:
 *   - Renders alias, linea1, ciudad, codigo_postal
 *   - Shows Badge "Predeterminada" when es_predeterminada === true
 *   - Does NOT show Badge when es_predeterminada === false
 *   - "Marcar predeterminada" button visible when es_predeterminada === false
 *   - "Marcar predeterminada" button NOT visible when es_predeterminada === true
 *   - Calls onEdit when "Editar" is clicked
 *   - Calls onDelete when "Eliminar" is clicked
 *   - Calls onSetPredeterminada when "Predeterminada" is clicked
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AddressCard } from '@/features/addresses/components/AddressCard'
import type { DireccionResponse } from '@/features/addresses/types'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const baseAddress: DireccionResponse = {
  id: 1,
  usuario_id: 2,
  alias: 'Casa',
  linea1: 'Av. Corrientes 1234',
  piso: null,
  departamento: null,
  ciudad: 'Buenos Aires',
  codigo_postal: '1043',
  referencia: null,
  es_predeterminada: false,
  creado_en: '2024-01-01T00:00:00',
  actualizado_en: '2024-01-01T00:00:00',
}

const defaultAddress: DireccionResponse = {
  ...baseAddress,
  id: 2,
  alias: 'Trabajo',
  es_predeterminada: true,
}

const addressWithExtras: DireccionResponse = {
  ...baseAddress,
  id: 3,
  alias: 'Departamento',
  piso: '5',
  departamento: 'B',
  referencia: 'Timbre B',
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('AddressCard', () => {
  const onEdit = vi.fn()
  const onDelete = vi.fn()
  const onSetPredeterminada = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders alias, linea1, ciudad and codigo_postal', () => {
    render(
      <AddressCard
        address={baseAddress}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    expect(screen.getByText('Casa')).toBeInTheDocument()
    expect(screen.getByText('Av. Corrientes 1234')).toBeInTheDocument()
    expect(screen.getByText(/Buenos Aires/)).toBeInTheDocument()
    expect(screen.getByText(/1043/)).toBeInTheDocument()
  })

  it('shows Badge "Predeterminada" when es_predeterminada is true', () => {
    render(
      <AddressCard
        address={defaultAddress}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    expect(screen.getByText('Predeterminada')).toBeInTheDocument()
  })

  it('does NOT show Badge when es_predeterminada is false', () => {
    render(
      <AddressCard
        address={baseAddress}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    // Badge is a <span> with role not="button" — only the button has the text in a non-badge element
    // Badge renders as <span> with class containing "rounded-full"
    const badge = document.querySelector('span.rounded-full')
    expect(badge).not.toBeInTheDocument()
  })

  it('"Marcar predeterminada" button visible when es_predeterminada is false', () => {
    render(
      <AddressCard
        address={baseAddress}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    expect(
      screen.getByRole('button', { name: /marcar/i }),
    ).toBeInTheDocument()
  })

  it('"Marcar predeterminada" button NOT visible when es_predeterminada is true', () => {
    render(
      <AddressCard
        address={defaultAddress}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    expect(
      screen.queryByRole('button', { name: /marcar/i }),
    ).not.toBeInTheDocument()
  })

  it('calls onEdit when "Editar" is clicked', () => {
    render(
      <AddressCard
        address={baseAddress}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /editar/i }))
    expect(onEdit).toHaveBeenCalledTimes(1)
  })

  it('calls onDelete when "Eliminar" is clicked', () => {
    render(
      <AddressCard
        address={baseAddress}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /eliminar/i }))
    expect(onDelete).toHaveBeenCalledTimes(1)
  })

  it('calls onSetPredeterminada when "Predeterminada" button is clicked', () => {
    render(
      <AddressCard
        address={baseAddress}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /marcar/i }))
    expect(onSetPredeterminada).toHaveBeenCalledTimes(1)
  })

  it('renders piso and departamento when provided', () => {
    render(
      <AddressCard
        address={addressWithExtras}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    expect(screen.getByText(/Piso 5/)).toBeInTheDocument()
    expect(screen.getByText(/Dpto. B/)).toBeInTheDocument()
  })

  it('renders referencia when provided', () => {
    render(
      <AddressCard
        address={addressWithExtras}
        onEdit={onEdit}
        onDelete={onDelete}
        onSetPredeterminada={onSetPredeterminada}
      />,
    )

    expect(screen.getByText(/Timbre B/)).toBeInTheDocument()
  })
})
