/**
 * useAddresses hook tests.
 *
 * Tests:
 *   - Returns list of addresses when API responds 200
 *   - isLoading is true during fetch
 *   - isError is true when API fails
 *
 * Strategy:
 *   - Mock apiClient.get with vi.mock
 *   - Wrap in QueryClientProvider with a fresh QueryClient per test (retry: false)
 *   - Use waitFor for async state assertions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useAddresses } from '@/features/addresses/hooks/useAddresses'
import type { DireccionResponse } from '@/features/addresses/types'

// ── Mock apiClient ────────────────────────────────────────────────────────────

vi.mock('@/shared/api/axios', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

import { apiClient } from '@/shared/api/axios'
const mockGet = apiClient.get as ReturnType<typeof vi.fn>

// ── Fixtures ──────────────────────────────────────────────────────────────────

const mockAddresses: DireccionResponse[] = [
  {
    id: 1,
    usuario_id: 2,
    alias: 'Casa',
    linea1: 'Av. Corrientes 1234',
    piso: null,
    departamento: null,
    ciudad: 'Buenos Aires',
    codigo_postal: '1043',
    referencia: null,
    es_predeterminada: true,
    creado_en: '2024-01-01T00:00:00',
    actualizado_en: '2024-01-01T00:00:00',
  },
  {
    id: 2,
    usuario_id: 2,
    alias: 'Trabajo',
    linea1: 'Florida 234',
    piso: '10',
    departamento: null,
    ciudad: 'Buenos Aires',
    codigo_postal: '1005',
    referencia: null,
    es_predeterminada: false,
    creado_en: '2024-01-02T00:00:00',
    actualizado_en: '2024-01-02T00:00:00',
  },
]

// ── Helper: fresh QueryClient per test ───────────────────────────────────────

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

describe('useAddresses', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns list of addresses when API responds 200', async () => {
    mockGet.mockResolvedValueOnce({ data: mockAddresses })

    const { result } = renderHook(() => useAddresses(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockAddresses)
    expect(result.current.data).toHaveLength(2)
    expect(mockGet).toHaveBeenCalledWith('/api/v1/direcciones')
  })

  it('isLoading is true during the request', async () => {
    // Never resolves during this check
    mockGet.mockReturnValueOnce(new Promise(() => {}))

    const { result } = renderHook(() => useAddresses(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()
  })

  it('isError is true when API fails', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network Error'))

    const { result } = renderHook(() => useAddresses(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.data).toBeUndefined()
  })
})
