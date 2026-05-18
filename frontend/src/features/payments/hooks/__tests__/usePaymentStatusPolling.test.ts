/**
 * Tests for usePaymentStatusPolling
 *
 * 12 required tests covering:
 *  1.  No polling if pedidoId === null
 *  2.  No polling if status !== 'waiting_payment'
 *  3.  isPolling === true when active
 *  4.  Stop + setStatus('success') on 'approved'
 *  5.  Stop + setStatus('error') on 'rejected'
 *  6.  Stop + setStatus('error') on 'cancelled'
 *  7.  Unknown estado → setStatus('error') + setError called
 *  8.  Cleanup on unmount (no more calls after unmount)
 *  9.  Retry increments retryCount
 * 10.  Retry exhausted → setError + isPolling === false
 * 11.  'pending' continues polling (3 calls in 60s)
 * 12.  First call is immediate (before any timer advance)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePaymentStatusPolling } from '../usePaymentStatusPolling'

// ---------------------------------------------------------------------------
// Mutable state for store mock — controlled per test
// ---------------------------------------------------------------------------

const mockSetStatus = vi.fn()
const mockSetError = vi.fn()

// storeStatus is read by the mock selector — change this variable to simulate
// different store states in individual tests
let currentStoreStatus = 'waiting_payment'

// ---------------------------------------------------------------------------
// Mocks — declared before all imports that use them
// ---------------------------------------------------------------------------

vi.mock('@/shared/api/axios', () => ({
  apiClient: { get: vi.fn() },
}))

vi.mock('@/store/paymentStore', () => ({
  usePaymentStore: vi.fn((selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      status: currentStoreStatus,
      setStatus: mockSetStatus,
      setError: mockSetError,
    }),
  ),
}))

// Import after mocks are registered
import { apiClient } from '@/shared/api/axios'

// Typed reference to the mocked apiClient.get
const mockGet = apiClient.get as ReturnType<typeof vi.fn>

// ---------------------------------------------------------------------------
// Setup / Teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.useFakeTimers()
  vi.clearAllMocks()
  // Reset store status to default (polling-active condition)
  currentStoreStatus = 'waiting_payment'
})

afterEach(() => {
  vi.useRealTimers()
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('usePaymentStatusPolling', () => {
  // Test 1
  it('no inicia polling si pedidoId es null', () => {
    const { result } = renderHook(() => usePaymentStatusPolling(null))
    expect(result.current.isPolling).toBe(false)
    expect(mockGet).not.toHaveBeenCalled()
  })

  // Test 2
  it('no inicia polling si status no es waiting_payment', () => {
    currentStoreStatus = 'idle'
    const { result } = renderHook(() => usePaymentStatusPolling(42))
    expect(result.current.isPolling).toBe(false)
    expect(mockGet).not.toHaveBeenCalled()
  })

  // Test 3
  it('isPolling es true cuando pedidoId y status son válidos', async () => {
    mockGet.mockResolvedValue({ data: { estado: 'pending' } })
    const { result } = renderHook(() => usePaymentStatusPolling(42))

    await act(async () => {
      await vi.runAllTicks()
    })

    expect(result.current.isPolling).toBe(true)
  })

  // Test 4
  it('detiene polling y llama setStatus("success") cuando approved', async () => {
    mockGet.mockResolvedValue({ data: { estado: 'approved' } })
    const { result } = renderHook(() => usePaymentStatusPolling(42))

    await act(async () => {
      await vi.runAllTicks()
    })

    expect(mockSetStatus).toHaveBeenCalledWith('success')
    expect(result.current.isPolling).toBe(false)
  })

  // Test 5
  it('detiene polling y llama setStatus("error") cuando rejected', async () => {
    mockGet.mockResolvedValue({ data: { estado: 'rejected' } })
    const { result } = renderHook(() => usePaymentStatusPolling(42))

    await act(async () => {
      await vi.runAllTicks()
    })

    expect(mockSetStatus).toHaveBeenCalledWith('error')
    expect(result.current.isPolling).toBe(false)
  })

  // Test 6
  it('detiene polling y llama setStatus("error") cuando cancelled', async () => {
    mockGet.mockResolvedValue({ data: { estado: 'cancelled' } })
    const { result } = renderHook(() => usePaymentStatusPolling(42))

    await act(async () => {
      await vi.runAllTicks()
    })

    expect(mockSetStatus).toHaveBeenCalledWith('error')
    expect(result.current.isPolling).toBe(false)
  })

  // Test 7
  it('estado desconocido → setStatus("error") + setError llamado', async () => {
    mockGet.mockResolvedValue({ data: { estado: 'unknown_status_xyz' } })
    const { result } = renderHook(() => usePaymentStatusPolling(42))

    await act(async () => {
      await vi.runAllTicks()
    })

    expect(mockSetStatus).toHaveBeenCalledWith('error')
    expect(mockSetError).toHaveBeenCalled()
    expect(result.current.isPolling).toBe(false)
  })

  // Test 8
  it('limpia el interval al desmontar (no más llamadas a API)', async () => {
    mockGet.mockResolvedValue({ data: { estado: 'pending' } })
    const { unmount } = renderHook(() => usePaymentStatusPolling(42))

    // Let first immediate call complete
    await act(async () => {
      await vi.runAllTicks()
    })

    const callsBeforeUnmount = mockGet.mock.calls.length
    expect(callsBeforeUnmount).toBeGreaterThan(0)

    unmount()

    // Advance timers past multiple intervals — no new calls should happen
    await act(async () => {
      vi.advanceTimersByTime(90_000)
      await vi.runAllTicks()
    })

    expect(mockGet.mock.calls.length).toBe(callsBeforeUnmount)
  })

  // Test 9
  it('incrementa retryCount en error de red', async () => {
    mockGet.mockRejectedValue(new Error('Network error'))
    const { result } = renderHook(() => usePaymentStatusPolling(42))

    // Flush the initial poll call which fails and schedules a retry
    await act(async () => {
      await vi.runAllTicks()
    })

    // Advance through the first retry delay (1000ms)
    await act(async () => {
      vi.advanceTimersByTime(1100)
      await vi.runAllTicks()
    })

    expect(result.current.retryCount).toBeGreaterThan(0)
  })

  // Test 10
  it('retries agotados → setError llamado e isPolling es false', async () => {
    mockGet.mockRejectedValue(new Error('Network error'))
    const { result } = renderHook(() => usePaymentStatusPolling(42))

    // The hook calls poll() immediately. Each failure schedules a setTimeout
    // for the retry delay. We need to advance timers and flush microtasks
    // multiple times to exhaust all 3 retries.
    // Delay schedule: retry 0 → 1000ms, retry 1 → 2000ms, retry 2 → 4000ms

    // Flush initial poll() rejection
    await act(async () => {
      await vi.runAllTicks()
    })

    // Trigger retry 1 (delay: 1000ms)
    await act(async () => {
      vi.advanceTimersByTime(1100)
      await vi.runAllTicks()
    })

    // Trigger retry 2 (delay: 2000ms)
    await act(async () => {
      vi.advanceTimersByTime(2100)
      await vi.runAllTicks()
    })

    // Trigger retry 3 (delay: 4000ms) — this is the last retry
    // After this one fails, retryCountRef.current === MAX_RETRIES → set error
    await act(async () => {
      vi.advanceTimersByTime(4100)
      await vi.runAllTicks()
    })

    // Give microtasks time to settle after the last rejection
    await act(async () => {
      await vi.runAllTicks()
    })

    expect(mockSetError).toHaveBeenCalled()
    expect(result.current.isPolling).toBe(false)
  })

  // Test 11
  it('pending continúa polling (3 llamadas en ~60s)', async () => {
    mockGet.mockResolvedValue({ data: { estado: 'pending' } })
    const { result } = renderHook(() => usePaymentStatusPolling(42))

    // Call 1: immediate on mount
    await act(async () => {
      await vi.runAllTicks()
    })
    expect(mockGet).toHaveBeenCalledTimes(1)

    // Call 2: after first POLL_INTERVAL_MS (30s)
    await act(async () => {
      vi.advanceTimersByTime(30_000)
      await vi.runAllTicks()
    })
    expect(mockGet).toHaveBeenCalledTimes(2)

    // Call 3: after second POLL_INTERVAL_MS (another 30s)
    await act(async () => {
      vi.advanceTimersByTime(30_000)
      await vi.runAllTicks()
    })
    expect(mockGet).toHaveBeenCalledTimes(3)

    // setStatus must NOT have been called — still pending
    expect(mockSetStatus).not.toHaveBeenCalled()
    expect(result.current.isPolling).toBe(true)
  })

  // Test 12
  it('primera llamada a API es inmediata al montar (sin avanzar timers)', () => {
    // Set up mock but do not resolve — we just verify the call was made
    let resolveFn!: (value: unknown) => void
    mockGet.mockReturnValue(
      new Promise((resolve) => {
        resolveFn = resolve
      }),
    )

    renderHook(() => usePaymentStatusPolling(42))

    // apiClient.get must have been called synchronously (before any timers advance)
    expect(mockGet).toHaveBeenCalledTimes(1)
    expect(mockGet).toHaveBeenCalledWith('/api/v1/pagos/42/status')

    // Resolve promise to avoid unhandled rejection warning
    act(() => {
      resolveFn({ data: { estado: 'pending' } })
    })
  })
})
