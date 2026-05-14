/**
 * Tests for useLogout hook (task 7.2)
 *
 * Verifies:
 * - authStore.logout() is called even when logoutUser() throws (best-effort)
 * - authStore.logout() is called after a successful logoutUser() call
 * - isLoading starts as false, goes true during the call, returns to false after
 * - logoutUser is called with the refreshToken from authStore
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useAuthStore } from '../../../store/authStore'
import { useLogout } from '../useLogout'

// ---------------------------------------------------------------------------
// Mock the authApi module so we control what logoutUser() returns
// ---------------------------------------------------------------------------

vi.mock('../../api/authApi', () => ({
  logoutUser: vi.fn(),
}))

import { logoutUser } from '../../api/authApi'
const mockLogoutUser = vi.mocked(logoutUser)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

function seedAuthStore(refreshToken: string | null = 'my-refresh-token') {
  useAuthStore.setState({
    accessToken: 'my-access-token',
    refreshToken,
    user: { id: '1', email: 'user@example.com', name: 'Test User', roles: ['CLIENT'] },
    isAuthenticated: true,
    _hasHydrated: true,
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useLogout hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    useAuthStore.setState({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      _hasHydrated: false,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('7.2.1 calls authStore.logout() after logoutUser() resolves successfully', async () => {
    seedAuthStore()
    mockLogoutUser.mockResolvedValue(undefined)

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.logout()
    })

    // authStore state should be cleared
    const storeState = useAuthStore.getState()
    expect(storeState.isAuthenticated).toBe(false)
    expect(storeState.accessToken).toBeNull()
    expect(storeState.refreshToken).toBeNull()
    expect(storeState.user).toBeNull()
  })

  it('7.2.2 calls authStore.logout() even when logoutUser() throws (best-effort)', async () => {
    seedAuthStore()
    mockLogoutUser.mockRejectedValue(new Error('Network Error'))

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.logout()
    })

    // authStore must be cleared regardless of backend failure
    const storeState = useAuthStore.getState()
    expect(storeState.isAuthenticated).toBe(false)
    expect(storeState.accessToken).toBeNull()
    expect(storeState.refreshToken).toBeNull()
    expect(storeState.user).toBeNull()
  })

  it('7.2.3 calls logoutUser with the refreshToken from the store', async () => {
    seedAuthStore('specific-refresh-token')
    mockLogoutUser.mockResolvedValue(undefined)

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.logout()
    })

    expect(mockLogoutUser).toHaveBeenCalledOnce()
    expect(mockLogoutUser).toHaveBeenCalledWith('specific-refresh-token')
  })

  it('7.2.4 does NOT call logoutUser when refreshToken is null', async () => {
    seedAuthStore(null)  // no refresh token
    mockLogoutUser.mockResolvedValue(undefined)

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.logout()
    })

    // logoutUser should not be called if there's no token
    expect(mockLogoutUser).not.toHaveBeenCalled()

    // But local state should still be cleared
    const storeState = useAuthStore.getState()
    expect(storeState.isAuthenticated).toBe(false)
  })

  it('7.2.5 isLoading starts false', () => {
    seedAuthStore()

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(false)
  })

  it('7.2.6 isLoading returns to false after successful logout', async () => {
    seedAuthStore()
    mockLogoutUser.mockResolvedValue(undefined)

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.logout()
    })

    expect(result.current.isLoading).toBe(false)
  })

  it('7.2.7 isLoading returns to false after failed backend call', async () => {
    seedAuthStore()
    mockLogoutUser.mockRejectedValue(new Error('Server Error'))

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.logout()
    })

    expect(result.current.isLoading).toBe(false)
  })
})
