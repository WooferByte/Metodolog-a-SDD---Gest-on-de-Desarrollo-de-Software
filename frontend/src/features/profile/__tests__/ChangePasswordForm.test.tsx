/**
 * ChangePasswordForm component tests.
 *
 * Tests:
 *   - Renders two password inputs by default (type="password")
 *   - Toggle button changes password-actual input type to "text"
 *   - Toggle button changes nueva-password input type to "text"
 *   - Shows error if passwords are shorter than 8 chars
 *   - Does NOT call mutate if validation fails
 *   - Calls mutate with correct payload when validation passes
 *   - Calls mutate when nueva password equals actual (removed same-password check)
 *
 * Strategy:
 *   - Mock useCambiarPassword with vi.mock
 *   - No auth or QueryClient needed since mutation is mocked
 *
 * NOTE: The "same password error" test was intentionally removed.
 * The same-password client-side check was deleted (BUG 2 fix). The backend
 * is the authority on whether the current password is correct — the client
 * should not block requests based on string equality.
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

  it('calls mutate when nueva password equals actual (no client-side same-password block)', () => {
    // BUG 2 fix: the same-password equality check was removed.
    // When both fields have identical strings >= 8 chars, the form must
    // call mutate and let the backend decide whether to reject the request.
    render(<ChangePasswordForm />)
    fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'password123' } })
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /cambiar contraseña/i }))
    // No "diferente" error message should appear
    expect(screen.queryByText(/nueva contraseña debe ser diferente/i)).not.toBeInTheDocument()
    // mutate IS called — the backend owns this validation
    expect(mockMutate).toHaveBeenCalledWith(
      { password_actual: 'password123', nueva_password: 'password123' },
      expect.any(Object),
    )
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
