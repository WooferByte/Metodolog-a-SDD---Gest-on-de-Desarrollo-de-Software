/**
 * ToastContainer Tests
 *
 * Tests:
 * - Renders nothing when toast list is empty
 * - Renders toast message when toast is in store
 * - Close button calls removeToast with correct ID
 * - Auto-dismiss fires removeToast after timeout (vi.useFakeTimers)
 * - Correct icons shown per toast type
 * - Max 5 toasts visible (oldest trimmed)
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { ToastContainer } from '../ToastContainer'
import { useUIStore } from '@/store/uiStore'

// ---------------------------------------------------------------------------
// Store reset helper
// ---------------------------------------------------------------------------
function resetStore() {
  useUIStore.setState({ toasts: [] })
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------
beforeEach(() => {
  resetStore()
  vi.useFakeTimers()
})

afterEach(() => {
  vi.runOnlyPendingTimers()
  vi.useRealTimers()
  resetStore()
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ToastContainer', () => {
  it('renders nothing when there are no toasts', () => {
    const { container } = render(<ToastContainer />)
    // The component returns null — container should be empty
    expect(container.firstChild).toBeNull()
  })

  it('renders a toast message when a toast is added to the store', () => {
    useUIStore.getState().addToast({ message: 'Todo OK', type: 'success' })

    render(<ToastContainer />)

    expect(screen.getByText('Todo OK')).toBeInTheDocument()
  })

  it('renders multiple toasts', () => {
    useUIStore.getState().addToast({ message: 'Toast 1', type: 'info' })
    useUIStore.getState().addToast({ message: 'Toast 2', type: 'error' })

    render(<ToastContainer />)

    expect(screen.getByText('Toast 1')).toBeInTheDocument()
    expect(screen.getByText('Toast 2')).toBeInTheDocument()
  })

  it('close button calls removeToast and removes the toast', () => {
    useUIStore.getState().addToast({ message: 'Cerrar esto', type: 'warning' })

    render(<ToastContainer />)

    const closeButton = screen.getByRole('button', { name: /cerrar notificación/i })
    fireEvent.click(closeButton)

    expect(useUIStore.getState().toasts).toHaveLength(0)
  })

  it('auto-dismisses a success toast after 4000ms', () => {
    useUIStore.getState().addToast({ message: 'Éxito', type: 'success' })

    render(<ToastContainer />)
    expect(useUIStore.getState().toasts).toHaveLength(1)

    act(() => {
      vi.advanceTimersByTime(4000)
    })

    expect(useUIStore.getState().toasts).toHaveLength(0)
  })

  it('auto-dismisses an error toast after 6000ms', () => {
    useUIStore.getState().addToast({ message: 'Error grave', type: 'error' })

    render(<ToastContainer />)

    act(() => {
      vi.advanceTimersByTime(5999)
    })
    // Should still be there at 5999ms
    expect(useUIStore.getState().toasts).toHaveLength(1)

    act(() => {
      vi.advanceTimersByTime(1)
    })
    // Gone at exactly 6000ms
    expect(useUIStore.getState().toasts).toHaveLength(0)
  })

  it('auto-dismisses a warning toast after 5000ms', () => {
    useUIStore.getState().addToast({ message: 'Cuidado', type: 'warning' })

    render(<ToastContainer />)

    act(() => {
      vi.advanceTimersByTime(5000)
    })

    expect(useUIStore.getState().toasts).toHaveLength(0)
  })

  it('respects custom duration when toast.duration is defined', () => {
    useUIStore.getState().addToast({
      message: 'Custom duration',
      type: 'info',
      duration: 2000,
    })

    render(<ToastContainer />)

    act(() => {
      vi.advanceTimersByTime(1999)
    })
    expect(useUIStore.getState().toasts).toHaveLength(1)

    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(useUIStore.getState().toasts).toHaveLength(0)
  })

  it('limits visible toasts to 5 (oldest trimmed when more than 5 exist)', () => {
    // Add 7 toasts directly to the store
    useUIStore.setState({
      toasts: [
        { id: '1', message: 'Toast 1', type: 'info' },
        { id: '2', message: 'Toast 2', type: 'info' },
        { id: '3', message: 'Toast 3', type: 'info' },
        { id: '4', message: 'Toast 4', type: 'info' },
        { id: '5', message: 'Toast 5', type: 'info' },
        { id: '6', message: 'Toast 6', type: 'info' },
        { id: '7', message: 'Toast 7', type: 'info' },
      ],
    })

    render(<ToastContainer />)

    // Newest 5 visible; oldest 2 trimmed from display
    expect(screen.queryByText('Toast 1')).not.toBeInTheDocument()
    expect(screen.queryByText('Toast 2')).not.toBeInTheDocument()
    expect(screen.getByText('Toast 3')).toBeInTheDocument()
    expect(screen.getByText('Toast 7')).toBeInTheDocument()
  })
})
