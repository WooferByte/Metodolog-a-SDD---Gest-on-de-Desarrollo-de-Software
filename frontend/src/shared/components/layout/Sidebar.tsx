/**
 * Sidebar — role-aware side navigation panel.
 *
 * Behavior:
 *   Mobile (< lg):  overlay with backdrop; closes on Escape or backdrop click
 *   Desktop (lg+):  persistent left panel that pushes main content (flex-row)
 *
 * State:
 *   - Visibility driven by uiStore.sidebarOpen / toggleSidebar
 *   - On lg+ screens, auto-opens on mount via matchMedia
 *
 * Links:
 *   - Uses useNavLinks() hook for role-aware links (same as Navbar)
 *
 * Accessibility:
 *   - role="navigation" with aria-label
 *   - Escape key closes on mobile
 *   - focus-trap not needed for overlay-style sidebar (focus stays inside
 *     because backdrop is not interactive on desktop)
 */

import { useEffect, useCallback } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useUIStore } from '@/store/uiStore'
import { useNavLinks } from '@/shared/hooks/useNavLinks'
import { cn } from '@/shared/lib/utils'

export function Sidebar() {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const navLinks = useNavLinks()
  const location = useLocation()

  // Auto-open on desktop (lg+) when component mounts
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1024px)')
    if (mq.matches && !sidebarOpen) {
      // Open sidebar on large screens without toggling if already managed
      useUIStore.setState({ sidebarOpen: true })
    }

    const handleChange = (e: MediaQueryListEvent) => {
      if (e.matches) {
        useUIStore.setState({ sidebarOpen: true })
      } else {
        useUIStore.setState({ sidebarOpen: false })
      }
    }

    mq.addEventListener('change', handleChange)
    return () => mq.removeEventListener('change', handleChange)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Close on Escape key (mobile overlay)
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && sidebarOpen) {
        const isMobile = !window.matchMedia('(min-width: 1024px)').matches
        if (isMobile) toggleSidebar()
      }
    },
    [sidebarOpen, toggleSidebar],
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  return (
    <>
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-foreground/40 lg:hidden"
          aria-hidden="true"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar panel */}
      <aside
        id="sidebar"
        aria-label="Navegación lateral"
        className={cn(
          // Base
          'fixed top-0 left-0 z-30 h-full w-64',
          'bg-card border-r border-border',
          'flex flex-col pt-16',
          'transition-transform duration-300 ease-in-out',
          // Mobile: slide in/out; Desktop: always visible in flow
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
          // On lg+, sidebar is part of the layout flow (not fixed overlay)
          'lg:static lg:translate-x-0 lg:h-auto lg:pt-0 lg:z-auto',
          !sidebarOpen && 'lg:hidden',
        )}
      >
        <nav
          role="navigation"
          aria-label="Menú lateral"
          className="flex-1 overflow-y-auto py-4"
        >
          <ul className="flex flex-col gap-1 px-3" role="list">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.to
              return (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    aria-current={isActive ? 'page' : undefined}
                    onClick={() => {
                      // Close sidebar on mobile after navigation
                      if (!window.matchMedia('(min-width: 1024px)').matches) {
                        useUIStore.setState({ sidebarOpen: false })
                      }
                    }}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2',
                      'text-sm font-medium transition-colors',
                      'hover:bg-accent hover:text-accent-foreground',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                      isActive
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground',
                    )}
                  >
                    {link.label}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
      </aside>
    </>
  )
}
