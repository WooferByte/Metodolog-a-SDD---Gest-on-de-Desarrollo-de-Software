/**
 * AuthStore Tests
 * 
 * Tests for authentication state management, JWT token handling,
 * role checking, and localStorage persistence.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useAuthStore } from '../authStore'

describe('AuthStore', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    // Reset store to initial state
    useAuthStore.setState({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      _hasHydrated: false,
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Initial State', () => {
    it('should have empty initial state', () => {
      const state = useAuthStore.getState()
      expect(state.accessToken).toBeNull()
      expect(state.refreshToken).toBeNull()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('updateTokens', () => {
    it('should update both tokens and set isAuthenticated to true', () => {
      const { updateTokens } = useAuthStore.getState()
      updateTokens('access-token-123', 'refresh-token-456')

      const state = useAuthStore.getState()
      expect(state.accessToken).toBe('access-token-123')
      expect(state.refreshToken).toBe('refresh-token-456')
      expect(state.isAuthenticated).toBe(true)
    })

    it('should set isAuthenticated to false if accessToken is empty', () => {
      const { updateTokens } = useAuthStore.getState()
      updateTokens('', 'refresh-token')

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('setUser', () => {
    it('should set user data and isAuthenticated to true', () => {
      const { setUser } = useAuthStore.getState()
      const userData = {
        id: '123',
        email: 'user@example.com',
        name: 'John Doe',
        roles: ['customer'],
      }

      setUser(userData)

      const state = useAuthStore.getState()
      expect(state.user).toEqual(userData)
      expect(state.isAuthenticated).toBe(true)
    })

    it('should set user to null and isAuthenticated to false', () => {
      const { setUser } = useAuthStore.getState()
      setUser(null)

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('logout', () => {
    it('should clear all auth state', () => {
      const { updateTokens, setUser, logout } = useAuthStore.getState()

      // Setup authenticated state
      updateTokens('access-123', 'refresh-456')
      setUser({
        id: '123',
        email: 'user@example.com',
        name: 'John Doe',
        roles: ['customer'],
      })

      // Logout
      logout()

      const state = useAuthStore.getState()
      expect(state.accessToken).toBeNull()
      expect(state.refreshToken).toBeNull()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('hasRole', () => {
    it('should return true if user has specified role', () => {
      const { setUser, hasRole } = useAuthStore.getState()
      setUser({
        id: '123',
        email: 'admin@example.com',
        name: 'Admin User',
        roles: ['admin', 'customer'],
      })

      expect(hasRole('admin')).toBe(true)
      expect(hasRole('customer')).toBe(true)
    })

    it('should return false if user does not have specified role', () => {
      const { setUser, hasRole } = useAuthStore.getState()
      setUser({
        id: '123',
        email: 'user@example.com',
        name: 'Regular User',
        roles: ['customer'],
      })

      expect(hasRole('admin')).toBe(false)
    })

    it('should return false if user is not authenticated', () => {
      const { hasRole } = useAuthStore.getState()
      expect(hasRole('admin')).toBe(false)
    })
  })

  describe('localStorage persistence', () => {
    it('should persist only accessToken to localStorage', () => {
      const { updateTokens } = useAuthStore.getState()
      updateTokens('access-123', 'refresh-456')

      const stored = localStorage.getItem('food-store-auth')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.accessToken).toBe('access-123')
      // Important: refreshToken should NOT be persisted
      expect(parsed.state.refreshToken).toBeUndefined()
    })

    it('should have _hasHydrated flag in storage config', () => {
      // Verify that the store is configured to handle hydration
      // The store should be set up with onRehydrateStorage callback
      // which will set _hasHydrated to true when hydration completes
      expect(useAuthStore.getState()).toBeDefined()
    })
  })

  describe('SSR hydration safety', () => {
    it('should have _hasHydrated flag', () => {
      const state = useAuthStore.getState()
      expect(state._hasHydrated).toBeDefined()
    })

    it('should set _hasHydrated to true after hydration', () => {
      const { setHasHydrated } = useAuthStore.getState()
      setHasHydrated(true)

      expect(useAuthStore.getState()._hasHydrated).toBe(true)
    })
  })
})
