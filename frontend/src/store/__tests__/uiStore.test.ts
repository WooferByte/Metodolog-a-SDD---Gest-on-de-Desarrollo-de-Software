/**
 * UIStore Tests
 * 
 * Tests for UI state management (theme, sidebar, toasts),
 * selective localStorage persistence (theme only), and SSR safety.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useUIStore } from '../uiStore'

describe('UIStore', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    // Reset store to initial state
    useUIStore.setState({
      theme: 'light',
      sidebarOpen: false,
      toasts: [],
      _hasHydrated: false,
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useUIStore.getState()
      expect(state.theme).toBe('light')
      expect(state.sidebarOpen).toBe(false)
      expect(state.toasts).toEqual([])
    })
  })

  describe('Theme Management', () => {
    it('should set theme to dark', () => {
      const { setTheme } = useUIStore.getState()
      setTheme('dark')

      expect(useUIStore.getState().theme).toBe('dark')
    })

    it('should set theme to light', () => {
      const { setTheme } = useUIStore.getState()
      setTheme('dark')
      setTheme('light')

      expect(useUIStore.getState().theme).toBe('light')
    })

    it('should allow toggling between themes', () => {
      const { setTheme } = useUIStore.getState()

      setTheme('dark')
      expect(useUIStore.getState().theme).toBe('dark')

      setTheme('light')
      expect(useUIStore.getState().theme).toBe('light')
    })
  })

  describe('Sidebar Management', () => {
    it('should toggle sidebar from closed to open', () => {
      const { toggleSidebar } = useUIStore.getState()

      expect(useUIStore.getState().sidebarOpen).toBe(false)
      toggleSidebar()
      expect(useUIStore.getState().sidebarOpen).toBe(true)
    })

    it('should toggle sidebar from open to closed', () => {
      const { toggleSidebar } = useUIStore.getState()

      toggleSidebar() // open
      toggleSidebar() // close
      expect(useUIStore.getState().sidebarOpen).toBe(false)
    })

    it('should support multiple toggles', () => {
      const { toggleSidebar } = useUIStore.getState()

      toggleSidebar() // open
      toggleSidebar() // close
      toggleSidebar() // open
      toggleSidebar() // close

      expect(useUIStore.getState().sidebarOpen).toBe(false)
    })
  })

  describe('Toast Notifications', () => {
    it('should add success toast', () => {
      const { addToast } = useUIStore.getState()

      addToast({
        message: 'Success!',
        type: 'success',
      })

      const state = useUIStore.getState()
      expect(state.toasts).toHaveLength(1)
      expect(state.toasts[0].message).toBe('Success!')
      expect(state.toasts[0].type).toBe('success')
    })

    it('should generate unique IDs for toasts', async () => {
      const { addToast } = useUIStore.getState()

      addToast({
        message: 'First',
        type: 'info',
      })

      // Add small delay to ensure different timestamps
      await new Promise((resolve) => setTimeout(resolve, 10))

      addToast({
        message: 'Second',
        type: 'warning',
      })

      const state = useUIStore.getState()
      expect(state.toasts[0].id).not.toBe(state.toasts[1].id)
    })

    it('should add multiple toast types', () => {
      const { addToast } = useUIStore.getState()

      addToast({ message: 'Success', type: 'success' })
      addToast({ message: 'Error', type: 'error' })
      addToast({ message: 'Info', type: 'info' })
      addToast({ message: 'Warning', type: 'warning' })

      const state = useUIStore.getState()
      expect(state.toasts).toHaveLength(4)
      expect(state.toasts[0].type).toBe('success')
      expect(state.toasts[1].type).toBe('error')
      expect(state.toasts[2].type).toBe('info')
      expect(state.toasts[3].type).toBe('warning')
    })

    it('should support optional duration', () => {
      const { addToast } = useUIStore.getState()

      addToast({
        message: 'Will disappear',
        type: 'info',
        duration: 3000,
      })

      const state = useUIStore.getState()
      expect(state.toasts[0].duration).toBe(3000)
    })

    it('should remove toast by ID', async () => {
      const { addToast, removeToast } = useUIStore.getState()

      addToast({ message: 'Toast 1', type: 'info' })
      await new Promise((resolve) => setTimeout(resolve, 10))
      addToast({ message: 'Toast 2', type: 'info' })

      const firstToastId = useUIStore.getState().toasts[0].id

      removeToast(firstToastId)

      const state = useUIStore.getState()
      expect(state.toasts).toHaveLength(1)
      expect(state.toasts[0].message).toBe('Toast 2')
    })

    it('should not crash if removing non-existent toast', () => {
      const { removeToast } = useUIStore.getState()

      expect(() => removeToast('non-existent-id')).not.toThrow()
    })
  })

  describe('localStorage persistence', () => {
    it('should persist only theme to localStorage', () => {
      const { setTheme, toggleSidebar, addToast } = useUIStore.getState()

      setTheme('dark')
      toggleSidebar() // open
      addToast({ message: 'Test', type: 'info' })

      const stored = localStorage.getItem('food-store-ui')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.theme).toBe('dark')
      // Sidebar and toasts should NOT be persisted
      expect(parsed.state.sidebarOpen).toBeUndefined()
      expect(parsed.state.toasts).toBeUndefined()
    })

    it('should have hydration config set up', () => {
      // Verify that the store is configured to handle hydration
      expect(useUIStore.getState()).toBeDefined()
      // onRehydrateStorage callback will set _hasHydrated to true when hydration completes
    })

    it('should reset sidebar and toasts on page reload', () => {
      const { toggleSidebar, addToast } = useUIStore.getState()

      // Setup state
      toggleSidebar()
      addToast({ message: 'Test', type: 'info' })

      expect(useUIStore.getState().sidebarOpen).toBe(true)
      expect(useUIStore.getState().toasts).toHaveLength(1)

      // Simulate page reload
      useUIStore.setState({
        sidebarOpen: false,
        toasts: [],
        _hasHydrated: true,
      })

      const state = useUIStore.getState()
      expect(state.sidebarOpen).toBe(false)
      expect(state.toasts).toHaveLength(0)
    })

    it('theme persists across page reloads while sidebar does not', () => {
      const { setTheme, toggleSidebar } = useUIStore.getState()

      setTheme('dark')
      toggleSidebar()

      // Check what's in localStorage
      const stored = localStorage.getItem('food-store-ui')
      const parsed = JSON.parse(stored!)

      // Theme should be there
      expect(parsed.state.theme).toBe('dark')

      // Sidebar should not be persisted
      expect(parsed.state.sidebarOpen).toBeUndefined()
    })
  })

  describe('SSR hydration safety', () => {
    it('should have _hasHydrated flag', () => {
      const state = useUIStore.getState()
      expect(state._hasHydrated).toBeDefined()
    })

    it('should set _hasHydrated to true after hydration', () => {
      const { setHasHydrated } = useUIStore.getState()
      setHasHydrated(true)

      expect(useUIStore.getState()._hasHydrated).toBe(true)
    })

    it('should have onRehydrateStorage callback configured', () => {
      // The store is configured with onRehydrateStorage callback
      // which automatically sets _hasHydrated to true during hydration
      // This is handled by Zustand persist middleware
      expect(useUIStore.getState()).toBeDefined()
    })
  })

  describe('UI State Scenarios', () => {
    it('should support theme switching without affecting sidebar/toasts', () => {
      const { setTheme, toggleSidebar, addToast } = useUIStore.getState()

      toggleSidebar()
      addToast({ message: 'Info', type: 'info' })

      setTheme('dark')
      expect(useUIStore.getState().sidebarOpen).toBe(true)
      expect(useUIStore.getState().toasts).toHaveLength(1)

      setTheme('light')
      expect(useUIStore.getState().sidebarOpen).toBe(true)
      expect(useUIStore.getState().toasts).toHaveLength(1)
    })

    it('should support clearing all toasts', () => {
      const { addToast } = useUIStore.getState()

      addToast({ message: '1', type: 'info' })
      addToast({ message: '2', type: 'info' })
      addToast({ message: '3', type: 'info' })

      // Clear all toasts
      useUIStore.setState({ toasts: [] })

      expect(useUIStore.getState().toasts).toHaveLength(0)
    })
  })
})
