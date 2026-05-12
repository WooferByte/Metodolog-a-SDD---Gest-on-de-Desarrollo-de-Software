/**
 * Tests for useNavLinks hook
 *
 * Strategy: mock useAuthStore with vi.mock and test the hook logic
 * directly via renderHook — no full component mounting required.
 *
 * Covers 5 auth states:
 *  1. user null             → 3 public links
 *  2. roles ["CLIENT"]      → 5 client links
 *  3. roles ["STOCK"]       → 3 stock links
 *  4. roles ["PEDIDOS"]     → 1 panel pedidos link
 *  5. roles ["ADMIN"]       → 6 admin links
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useNavLinks } from '../useNavLinks'
import type { AuthStore } from '../../../store/types'

// ---------------------------------------------------------------------------
// Mock the entire authStore module — we only need to control two selectors:
//   s._hasHydrated  and  s.user?.roles
// ---------------------------------------------------------------------------

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

import { useAuthStore } from '@/store/authStore'
const mockUseAuthStore = vi.mocked(useAuthStore)

/**
 * Helper: configure the mock so that the two selector calls inside
 * useNavLinks return the desired values.
 *
 * useNavLinks calls useAuthStore twice in order:
 *   1. (s) => s._hasHydrated
 *   2. (s) => s.user?.roles ?? []
 */
function mockAuthState({
  hasHydrated = true,
  roles = [] as string[],
} = {}) {
  const fakeState = {
    _hasHydrated: hasHydrated,
    user: roles.length
      ? ({ id: '1', email: 'u@test.com', name: 'Test', roles } as AuthStore['user'])
      : null,
  } as AuthStore

  mockUseAuthStore
    .mockImplementationOnce((selector: (s: AuthStore) => unknown) => selector(fakeState))
    .mockImplementationOnce((selector: (s: AuthStore) => unknown) => selector(fakeState))
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useNavLinks hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('1. user null → returns 3 public links', () => {
    mockAuthState({ hasHydrated: true, roles: [] })

    const { result } = renderHook(() => useNavLinks())
    const links = result.current

    expect(links).toHaveLength(3)
    const labels = links.map((l) => l.label)
    expect(labels).toContain('Catálogo')
    expect(labels).toContain('Iniciar sesión')
    expect(labels).toContain('Registrarse')
  })

  it('2. roles ["CLIENT"] → returns 5 client links', () => {
    mockAuthState({ hasHydrated: true, roles: ['CLIENT'] })

    const { result } = renderHook(() => useNavLinks())
    const links = result.current

    expect(links).toHaveLength(5)
    const paths = links.map((l) => l.to)
    expect(paths).toContain('/cart')
    expect(paths).toContain('/orders')
    expect(paths).toContain('/profile')
    expect(paths).toContain('/addresses')
  })

  it('3. roles ["STOCK"] → returns 3 stock links', () => {
    mockAuthState({ hasHydrated: true, roles: ['STOCK'] })

    const { result } = renderHook(() => useNavLinks())
    const links = result.current

    expect(links).toHaveLength(3)
    const paths = links.map((l) => l.to)
    expect(paths).toContain('/admin/productos')
    expect(paths).toContain('/admin/categorias')
    expect(paths).toContain('/admin/ingredientes')
  })

  it('4. roles ["PEDIDOS"] → returns 1 link (Panel Pedidos)', () => {
    mockAuthState({ hasHydrated: true, roles: ['PEDIDOS'] })

    const { result } = renderHook(() => useNavLinks())
    const links = result.current

    expect(links).toHaveLength(1)
    expect(links[0].to).toBe('/admin/pedidos')
  })

  it('5. roles ["ADMIN"] → returns 6 admin links', () => {
    mockAuthState({ hasHydrated: true, roles: ['ADMIN'] })

    const { result } = renderHook(() => useNavLinks())
    const links = result.current

    expect(links).toHaveLength(6)
    const paths = links.map((l) => l.to)
    expect(paths).toContain('/admin/usuarios')
    expect(paths).toContain('/admin/metricas')
    expect(paths).toContain('/admin/configuracion')
  })
})
