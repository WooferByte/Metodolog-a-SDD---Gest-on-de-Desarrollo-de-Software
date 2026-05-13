/**
 * usePerfil hook tests.
 *
 * Tests:
 *   - Returns data correctly when API responds 200
 *   - isLoading is true during the request
 *   - isError is true when the API fails
 *
 * Strategy:
 *   - Mock apiClient.get with vi.mock
 *   - Wrap in QueryClientProvider with a fresh QueryClient per test
 *   - Use waitFor for async state assertions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { usePerfil } from '@/features/profile/hooks/usePerfil'
import type { PerfilData } from '@/features/profile/types/profile'

// ── Mock apiClient ────────────────────────────────────────────────────────────

vi.mock('@/shared/api/axios', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

import { apiClient } from '@/shared/api/axios'
const mockGet = apiClient.get as ReturnType<typeof vi.fn>

// ── Fixture ───────────────────────────────────────────────────────────────────

const mockPerfil: PerfilData = {
  id: 2,
  email: 'cliente@test.com',
  nombre: 'Cliente Test',
  telefono: '1234567890',
  roles: ['CLIENT'],
  creado_en: '2025-01-01T00:00:00Z',
}

// ── Helper: create wrapper with fresh QueryClient per test ─────────────────────

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (QueryClientProvider as any)({ client: qc, children })
    )
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('usePerfil', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns data correctly when API responds 200', async () => {
    mockGet.mockResolvedValueOnce({ data: mockPerfil })

    const { result } = renderHook(() => usePerfil(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockPerfil)
    expect(mockGet).toHaveBeenCalledWith('/api/v1/perfil')
  })

  it('isLoading is true during the request', async () => {
    // Never resolves during this check
    mockGet.mockReturnValueOnce(new Promise(() => {}))

    const { result } = renderHook(() => usePerfil(), {
      wrapper: createWrapper(),
    })

    // Initially pending
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()
  })

  it('isError is true when API fails', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network Error'))

    const { result } = renderHook(() => usePerfil(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.data).toBeUndefined()
  })
})
