/**
 * EditProfileForm component tests.
 *
 * Tests:
 *   - Renders pre-populated fields with perfil data
 *   - Form-level error shown if no field was modified (dirty check)
 *   - Shows error inline if nombre is empty after user clears it
 *   - Shows error if telefono exceeds 20 characters
 *   - Calls mutate with correct payload when validation passes
 *   - Does NOT call mutate when validation fails
 *
 * Strategy:
 *   - Mock useUpdatePerfil with vi.mock
 *   - Wrap in QueryClientProvider + MemoryRouter
 *   - Use userEvent for form interactions
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { EditProfileForm } from '@/features/profile/components/EditProfileForm'
import type { PerfilData } from '@/features/profile/types/profile'

// ── Mock hooks ────────────────────────────────────────────────────────────────

const mockMutate = vi.fn()

vi.mock('@/features/profile/hooks/useUpdatePerfil', () => ({
  useUpdatePerfil: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}))

// ── Fixture ───────────────────────────────────────────────────────────────────

const mockPerfil: PerfilData = {
  id: 2,
  email: 'cliente@test.com',
  nombre: 'Juan Test',
  telefono: '1234567890',

  creado_en: '2024-01-01T00:00:00',
  activo: true,
}

// ── Helper ────────────────────────────────────────────────────────────────────

function Wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient()
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

function renderForm(perfil = mockPerfil, isLoading = false) {
  return render(
    <EditProfileForm perfil={perfil} isLoading={isLoading} />,
    { wrapper: Wrapper },
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('EditProfileForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders pre-populated fields with perfil data', () => {
    renderForm()
    expect(screen.getByLabelText('Nombre')).toHaveValue('Juan Test')
    expect(screen.getByLabelText('Teléfono')).toHaveValue('1234567890')
  })

  it('shows form-level error if no field was modified (dirty check)', () => {
    renderForm()
    // Submit without changing anything
    fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }))
    expect(screen.getByText(/modificá al menos un campo/i)).toBeInTheDocument()
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('shows error if nombre is explicitly cleared', () => {
    renderForm()
    const nombreInput = screen.getByLabelText('Nombre')
    // Clear the nombre field
    fireEvent.change(nombreInput, { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }))
    expect(screen.getByText(/nombre no puede estar vacío/i)).toBeInTheDocument()
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('shows error if telefono exceeds 20 characters', () => {
    renderForm()
    const telefonoInput = screen.getByLabelText('Teléfono')
    fireEvent.change(telefonoInput, { target: { value: '123456789012345678901' } }) // 21 chars
    fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }))
    expect(screen.getByText(/no puede superar los 20 caracteres/i)).toBeInTheDocument()
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('calls mutate with correct payload when only nombre changes', () => {
    renderForm()
    const nombreInput = screen.getByLabelText('Nombre')
    fireEvent.change(nombreInput, { target: { value: 'Nuevo Nombre' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }))
    expect(mockMutate).toHaveBeenCalledWith({ nombre: 'Nuevo Nombre' })
  })

  it('calls mutate with both fields when both are changed', () => {
    renderForm()
    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Nuevo Nombre' } })
    fireEvent.change(screen.getByLabelText('Teléfono'), { target: { value: '9876543210' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }))
    expect(mockMutate).toHaveBeenCalledWith({
      nombre: 'Nuevo Nombre',
      telefono: '9876543210',
    })
  })
})
