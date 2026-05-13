/**
 * ChangePasswordForm component tests.
 *
 * Tests:
 *   - Renders two password inputs by default (type="password")
 *   - Toggle button changes password-actual input type to "text"
 *   - Toggle button changes nueva-password input type to "text"
 *   - Shows error if nueva contraseña equals actual
 *   - Shows error if passwords are shorter than 8 chars
 *   - Does NOT call mutate if validation fails
 *   - Calls mutate with correct payload when validation passes
 *
 * Strategy:
 *   - Mock useCambiarPassword with vi.mock
 *   - No auth or QueryClient needed since mutation is mocked
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ChangePasswordForm } from '@/features/profile/components/ChangePasswordForm'

// ── Mock hook ─────────────────────────────────────────────────────────────────

const mockMutate = vi.fn()

vi.mock('@/features/profile/hooks/useCambiarPassword', () => ({
  useCambiarPassword: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}))

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ChangePasswordForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders two password inputs of type password by default', () => {
    render(<ChangePasswordForm />)
    expect(screen.getByLabelText('Contraseña actual')).toHaveAttribute('type', 'password')
    expect(screen.getByLabelText('Nueva contraseña')).toHaveAttribute('type', 'password')
  })

  it('toggle shows password-actual input (changes type to text)', () => {
    render(<ChangePasswordForm />)
    const toggle = screen.getByRole('button', { name: /mostrar contraseña actual/i })
    fireEvent.click(toggle)
    expect(screen.getByLabelText('Contraseña actual')).toHaveAttribute('type', 'text')
  })

  it('toggle shows nueva-password input (changes type to text)', () => {
    render(<ChangePasswordForm />)
    const toggle = screen.getByRole('button', { name: /mostrar nueva contraseña/i })
    fireEvent.click(toggle)
    expect(screen.getByLabelText('Nueva contraseña')).toHaveAttribute('type', 'text')
  })

  it('shows error when nueva password equals actual', () => {
    render(<ChangePasswordForm />)
    fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'password123' } })
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /cambiar contraseña/i }))
    expect(screen.getByText(/nueva contraseña debe ser diferente/i)).toBeInTheDocument()
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('shows error when passwords are shorter than 8 chars', () => {
    render(<ChangePasswordForm />)
    fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'short' } })
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'also' } })
    fireEvent.click(screen.getByRole('button', { name: /cambiar contraseña/i }))
    // Both fields have errors — use getAllByText since multiple messages match
    const errorMessages = screen.getAllByText(/al menos 8 caracteres/i)
    expect(errorMessages.length).toBeGreaterThanOrEqual(1)
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('does not call mutate when validation fails (empty fields)', () => {
    render(<ChangePasswordForm />)
    fireEvent.click(screen.getByRole('button', { name: /cambiar contraseña/i }))
    expect(mockMutate).not.toHaveBeenCalled()
    expect(screen.getByText(/contraseña actual es requerida/i)).toBeInTheDocument()
  })

  it('calls mutate with correct payload when validation passes', () => {
    render(<ChangePasswordForm />)
    fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'OldPass123' } })
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'NewPass456' } })
    fireEvent.click(screen.getByRole('button', { name: /cambiar contraseña/i }))
    expect(mockMutate).toHaveBeenCalledWith(
      { password_actual: 'OldPass123', nueva_password: 'NewPass456' },
      expect.any(Object),
    )
  })
})
