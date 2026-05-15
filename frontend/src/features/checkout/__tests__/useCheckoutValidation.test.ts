/**
 * Tests for useCheckoutValidation hook (tasks 11.1–11.3).
 *
 * 11.2 Mutation calls the correct endpoint with the assembled payload.
 * 11.3 onError triggers a toast via UIStore.
 *
 * Strategy:
 *   - Mock apiClient.post via vi.mock('@/shared/api/axios')
 *   - Control cartStore state via setState
 *   - Verify UIStore.addToast is called on error
 *   - Use @testing-library/react renderHook + act
 *   - Wrap in QueryClientProvider (TanStack Query v5 requirement)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock apiClient before importing the hook
vi.mock('@/shared/api/axios', () => ({
  apiClient: {
    post: vi.fn(),
  },
}))

// Import after mock is set up
import { apiClient } from '@/shared/api/axios'
import { useCheckoutValidation } from '../hooks/useCheckoutValidation'
import { useCartStore } from '@/store/cartStore'
import { useUIStore } from '@/store/uiStore'
import type { CartItem } from '@/store/types'
import type { ValidarCarritoResponse } from '../types'

// ---------------------------------------------------------------------------
// Test wrapper
// ---------------------------------------------------------------------------

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MOCK_RESPONSE: ValidarCarritoResponse = {
  stock_insuficiente: [],
  productos_invalidos: [],
  cambios_de_precio: [],
  carrito_vacio: false,
  sin_direccion: false,
}

function seedCart(items: CartItem[]) {
  useCartStore.setState({ items })
}

// ---------------------------------------------------------------------------
// Setup / Teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks()
  useCartStore.setState({ items: [] })
  // Reset toasts using the removeToast action or setState with full compatible type
  const state = useUIStore.getState()
  state.toasts.forEach((t) => state.removeToast(t.id))
})

afterEach(() => {
  useCartStore.setState({ items: [] })
})

// ---------------------------------------------------------------------------
// 11.2 — Mutation calls correct endpoint with correct payload
// ---------------------------------------------------------------------------

describe('useCheckoutValidation — mutation endpoint and payload', () => {
  it('calls POST /api/v1/pedidos/validar with mapped cart items', async () => {
    const mockPost = vi.mocked(apiClient.post)
    mockPost.mockResolvedValueOnce({ data: MOCK_RESPONSE })

    const cartItem: CartItem = {
      productId: '42',
      name: 'Pizza',
      price: 150.0,
      precio_carrito: 150.0,
      quantity: 2,
    }
    seedCart([cartItem])

    const { result } = renderHook(() => useCheckoutValidation(), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      result.current.mutate()
      // Wait for mutation to settle
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(mockPost).toHaveBeenCalledTimes(1)
    const [url, payload] = mockPost.mock.calls[0] as [string, { items: Array<{ producto_id: number; cantidad: number; precio_carrito: number }>; direccion_id: number }]
    expect(url).toBe('/api/v1/pedidos/validar')
    expect(payload.items).toHaveLength(1)
    expect(payload.items[0]).toMatchObject({
      producto_id: 42, // string → number conversion
      cantidad: 2,
      precio_carrito: 150.0,
    })
  })

  it('falls back to item.price when precio_carrito is undefined', async () => {
    const mockPost = vi.mocked(apiClient.post)
    mockPost.mockResolvedValueOnce({ data: MOCK_RESPONSE })

    const cartItem: CartItem = {
      productId: '10',
      name: 'Burger',
      price: 200.0,
      // No precio_carrito
      quantity: 1,
    }
    seedCart([cartItem])

    const { result } = renderHook(() => useCheckoutValidation(), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      result.current.mutate()
      await new Promise((r) => setTimeout(r, 50))
    })

    const [, payload] = mockPost.mock.calls[0] as [string, { items: Array<{ producto_id: number; precio_carrito: number }> }]
    expect(payload.items[0].precio_carrito).toBe(200.0)
  })

  it('returns validation data on success', async () => {
    const mockPost = vi.mocked(apiClient.post)
    const successResponse: ValidarCarritoResponse = {
      ...MOCK_RESPONSE,
      stock_insuficiente: [
        { producto_id: 1, nombre: 'Producto', stock_actual: 2, cantidad_solicitada: 5 },
      ],
    }
    mockPost.mockResolvedValueOnce({ data: successResponse })

    seedCart([
      { productId: '1', name: 'P', price: 100, precio_carrito: 100, quantity: 5 },
    ])

    const { result } = renderHook(() => useCheckoutValidation(), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      result.current.mutate()
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(result.current.data?.stock_insuficiente).toHaveLength(1)
    expect(result.current.isError).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// 11.3 — onError triggers toast
// ---------------------------------------------------------------------------

describe('useCheckoutValidation — error handling', () => {
  it('shows a toast when the API call fails', async () => {
    const mockPost = vi.mocked(apiClient.post)
    mockPost.mockRejectedValueOnce(new Error('Network Error'))

    seedCart([
      { productId: '1', name: 'P', price: 100, precio_carrito: 100, quantity: 1 },
    ])

    const { result } = renderHook(() => useCheckoutValidation(), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      result.current.mutate()
      await new Promise((r) => setTimeout(r, 100))
    })

    expect(result.current.isError).toBe(true)

    const toasts = useUIStore.getState().toasts
    expect(toasts.length).toBeGreaterThan(0)
    expect(toasts[0].type).toBe('error')
    expect(toasts[0].message).toContain('carrito')
  })
})
