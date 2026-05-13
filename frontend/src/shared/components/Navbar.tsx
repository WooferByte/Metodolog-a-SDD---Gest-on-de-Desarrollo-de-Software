/**
 * Navbar — top bar: brand, sidebar toggle, user info, theme toggle.
 *
 * Navigation links are NOT rendered here — the Sidebar handles all
 * navigation in every breakpoint (mobile overlay + desktop persistent).
 *
 * Layout:
 *   Left:  [☰ Hamburger] [Food Store]
 *   Right: [user@email] [Cerrar sesión] [🌙 Theme toggle]
 *
 * All styles use Tailwind v4 utility classes — zero inline style props.
 */

import { Link } from 'react-router-dom'
import { Menu, X, Moon, Sun } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'
import { useLogout } from '@/shared/hooks/useLogout'

export default function Navbar() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const { logout, isLoading } = useLogout()

  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const theme = useUIStore((s) => s.theme)
  const setTheme = useUIStore((s) => s.setTheme)

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  return (
    <nav className="bg-gray-900 text-white flex items-center justify-between px-4 py-3 z-40 relative">
      {/* Left: Hamburger + Brand */}
      <div className="flex items-center gap-3">
        {/* Hamburger — opens/closes Sidebar in all breakpoints */}
        <button
          onClick={toggleSidebar}
          aria-label={sidebarOpen ? 'Cerrar menú' : 'Abrir menú'}
          aria-expanded={sidebarOpen}
          aria-controls="sidebar"
          className="p-1.5 rounded-md text-gray-300 hover:text-white hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
        >
          {sidebarOpen ? (
            <X className="h-5 w-5" aria-hidden="true" />
          ) : (
            <Menu className="h-5 w-5" aria-hidden="true" />
          )}
        </button>

        {/* Brand */}
        <Link to="/" className="font-bold text-lg text-white no-underline shrink-0">
          Food Store
        </Link>
      </div>

      {/* Right: User info + theme toggle */}
      <div className="flex items-center gap-4">
        {isAuthenticated && (
          <>
            <span className="text-gray-400 text-sm select-none hidden sm:inline">
              {user?.email ?? user?.name}
            </span>

            <button
              onClick={logout}
              disabled={isLoading}
              className="px-3 py-1.5 bg-destructive hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed text-destructive-foreground text-sm font-medium rounded transition-colors"
              aria-busy={isLoading}
              aria-label="Cerrar sesión"
            >
              {isLoading ? 'Saliendo...' : 'Cerrar sesión'}
            </button>
          </>
        )}

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          aria-label={theme === 'light' ? 'Activar modo oscuro' : 'Activar modo claro'}
          className="p-1.5 rounded-md text-gray-300 hover:text-white hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
        >
          {theme === 'light' ? (
            <Moon className="h-5 w-5" aria-hidden="true" />
          ) : (
            <Sun className="h-5 w-5" aria-hidden="true" />
          )}
        </button>
      </div>
    </nav>
  )
}
