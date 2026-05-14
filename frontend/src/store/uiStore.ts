/**
 * UIStore - UI preferences and notifications
 * 
 * Features:
 * - Theme management (light/dark) with persistence
 * - Sidebar visibility (ephemeral - resets on reload)
 * - Toast notifications queue (ephemeral - cleared on reload)
 * - Selective persistence: ONLY theme is saved to localStorage
 * - SSR-safe hydration with _hasHydrated flag
 * 
 * Persistence behavior:
 * - Persists: theme preference (survives page reload)
 * - Does NOT persist: sidebarOpen, toasts (reset on reload)
 * 
 * Usage:
 * ```typescript
 * const theme = useUIStore((state) => state.theme)
 * const setTheme = useUIStore((state) => state.setTheme)
 * const addToast = useUIStore((state) => state.addToast)
 * const { sidebarOpen, toggleSidebar } = useUIStore()
 * ```
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { UIStore } from './types'

/**
 * Create uiStore with TypeScript support and selective localStorage persistence
 * 
 * Important: Uses create<T>()() double parentheses for middleware compatibility
 * Uses partialize to persist ONLY theme, leaving sidebar and toasts ephemeral
 */
export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      // Initial state
      theme: 'light',
      sidebarOpen: false,
      cartDrawerOpen: false,
      toasts: [],
      _hasHydrated: false,

      // Action: Set theme (light or dark)
      setTheme: (theme: UIStore['theme']) => set({ theme }),

      // Action: Toggle sidebar visibility
      toggleSidebar: () =>
        set((state) => ({
          sidebarOpen: !state.sidebarOpen,
        })),

      // Action: Toggle cart drawer visibility
      toggleCartDrawer: () =>
        set((state) => ({
          cartDrawerOpen: !state.cartDrawerOpen,
        })),

      // Action: Set cart drawer open/close explicitly
      setCartDrawerOpen: (open: boolean) => set({ cartDrawerOpen: open }),

      // Action: Add toast notification
      // Generates unique ID for toast using crypto.randomUUID (available in
      // all modern browsers and jsdom test environments).
      addToast: (toast) =>
        set((state) => ({
          toasts: [
            ...state.toasts,
            {
              ...toast,
              id: typeof crypto !== 'undefined' && crypto.randomUUID
                ? crypto.randomUUID()
                : `${Date.now()}-${Math.random().toString(36).slice(2)}`,
            },
          ],
        })),

      // Action: Remove toast by ID
      removeToast: (toastId: string) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== toastId),
        })),

      // Action: Set hydration flag for SSR safety
      setHasHydrated: (hydrated: boolean) =>
        set({ _hasHydrated: hydrated }),
    }),
    {
      name: 'food-store-ui', // unique key in localStorage
      storage: createJSONStorage(() => localStorage),
      // Important: Only persist theme
      // sidebar and toasts are ephemeral (reset on page reload)
      partialize: (state) => ({
        theme: state.theme,
        _hasHydrated: true,
      }),
      // Called when store is rehydrated from localStorage
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    },
  ),
)
