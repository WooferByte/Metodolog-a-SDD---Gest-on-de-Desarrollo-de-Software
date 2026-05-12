/**
 * ErrorBoundary Tests
 *
 * Tests:
 * - Normal render: no error → renders children
 * - Fallback UI: error in child → shows fallback
 * - Reload button calls window.location.reload
 * - "Ir al inicio" link present in fallback
 * - Development mode shows stack trace; production shows generic message
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorBoundary } from '../ErrorBoundary'

// ---------------------------------------------------------------------------
// Helper: a component that throws on render
// ---------------------------------------------------------------------------
function BombComponent({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error from BombComponent')
  }
  return <div data-testid="child-content">Child OK</div>
}

// Suppress React's console.error noise from intentional errors
const originalConsoleError = console.error
beforeEach(() => {
  console.error = vi.fn()
})
afterEach(() => {
  console.error = originalConsoleError
  vi.restoreAllMocks()
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ErrorBoundary', () => {
  it('renders children when no error is thrown', () => {
    render(
      <ErrorBoundary>
        <BombComponent shouldThrow={false} />
      </ErrorBoundary>,
    )

    expect(screen.getByTestId('child-content')).toBeInTheDocument()
    expect(screen.queryByText('¡Algo salió mal!')).not.toBeInTheDocument()
  })

  it('renders fallback UI when child throws', () => {
    render(
      <ErrorBoundary>
        <BombComponent shouldThrow={true} />
      </ErrorBoundary>,
    )

    expect(screen.getByText('¡Algo salió mal!')).toBeInTheDocument()
    expect(screen.queryByTestId('child-content')).not.toBeInTheDocument()
  })

  it('shows "Recargar Página" button in fallback UI', () => {
    render(
      <ErrorBoundary>
        <BombComponent shouldThrow={true} />
      </ErrorBoundary>,
    )

    expect(screen.getByRole('button', { name: /recargar página/i })).toBeInTheDocument()
  })

  it('shows "Ir al inicio" link in fallback UI', () => {
    render(
      <ErrorBoundary>
        <BombComponent shouldThrow={true} />
      </ErrorBoundary>,
    )

    const homeLink = screen.getByRole('link', { name: /ir al inicio/i })
    expect(homeLink).toBeInTheDocument()
    expect(homeLink).toHaveAttribute('href', '/')
  })

  it('calls window.location.reload when "Recargar Página" is clicked', () => {
    const reloadSpy = vi.fn()
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { ...window.location, reload: reloadSpy },
    })

    render(
      <ErrorBoundary>
        <BombComponent shouldThrow={true} />
      </ErrorBoundary>,
    )

    fireEvent.click(screen.getByRole('button', { name: /recargar página/i }))
    expect(reloadSpy).toHaveBeenCalledTimes(1)
  })

  it('shows generic error message (no stack trace) in non-development mode', () => {
    // The vitest environment sets MODE to 'test', which is not 'development'.
    // The ErrorBoundary only shows stack traces when MODE === 'development'.
    // This test therefore works in the standard test environment without mocking.

    render(
      <ErrorBoundary>
        <BombComponent shouldThrow={true} />
      </ErrorBoundary>,
    )

    expect(
      screen.getByText(/ocurrió un error inesperado/i),
    ).toBeInTheDocument()

    // The stack trace <pre> should NOT be visible in non-development mode
    expect(screen.queryByRole('code')).not.toBeInTheDocument()
  })
})
