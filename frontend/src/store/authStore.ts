/**
 * AuthStore - JWT token management and user authentication state
 *
 * Features:
 * - Manage JWT access and refresh tokens
 * - Store user data and roles
 * - Persist accessToken to localStorage (refreshToken NOT persisted for security)
 * - Helper methods for role checking
 * - SSR-safe hydration with _hasHydrated flag
 * - Redux DevTools integration via devtools middleware
 *
 * Usage:
 * ```typescript
 * const { isAuthenticated, user, hasRole } = useAuthStore()
 * const updateTokens = useAuthStore((state) => state.updateTokens)
 * const logout = useAuthStore((state) => state.logout)
 * ```
 */

import { create } from 'zustand'
import { persist, createJSONStorage, devtools } from 'zustand/middleware'
import type { AuthStore } from './types'

/**
 * Create authStore with TypeScript support, localStorage persistence, and devtools.
 *
 * Middleware order (Zustand v5): devtools(persist(...))
 * - devtools wraps persist so Redux DevTools sees the full state tree
 * - persist handles rehydration from localStorage
 *
 * Important: Uses create<T>()() double parentheses for middleware compatibility
 */
export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        accessToken: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
        _hasHydrated: false,

        // Action: Update both access and refresh tokens
        // Only accessToken will be persisted (see partialize below)
        updateTokens: (accessToken: string, refreshToken: string) =>
          set({
            accessToken,
            refreshToken,
            isAuthenticated: !!accessToken,
          }),

        // Action: Set user data
        setUser: (user) =>
          set({
            user,
            isAuthenticated: !!user,
          }),

        // Action: Logout - clear all auth state
        logout: () =>
          set({
            accessToken: null,
            refreshToken: null,
            user: null,
            isAuthenticated: false,
          }),

        // Action: Set hydration flag for SSR safety
        setHasHydrated: (hydrated: boolean) =>
          set({ _hasHydrated: hydrated }),

        // Helper: Check if user has specific role
        // Returns false if user is not authenticated
        hasRole: (role: string) => {
          const state = get()
          if (!state.user) return false
          return state.user.roles.includes(role)
        },
      }),
      {
        name: 'food-store-auth', // unique key in localStorage
        storage: createJSONStorage(() => localStorage),
        // Important: Only persist accessToken (NOT refreshToken) for security
        // refreshToken should never be stored in localStorage if possible
        partialize: (state) => ({
          accessToken: state.accessToken,
          user: state.user,
          isAuthenticated: state.isAuthenticated,
          _hasHydrated: true,
        }),
        // Called when store is rehydrated from localStorage
        onRehydrateStorage: () => (state) => {
          state?.setHasHydrated(true)
        },
      },
    ),
    { name: 'AuthStore' },
  ),
)
