/**
 * Navbar — top navigation bar with role-based dynamic links.
 *
 * Renders a different set of nav links depending on the authenticated
 * user's role, computed by the `useNavLinks` hook.
 *
 * - Unauthenticated: public links (Catálogo, Iniciar sesión, Registrarse)
 * - CLIENT: customer-facing links
 * - STOCK: inventory management links
 * - PEDIDOS: order panel link
 * - ADMIN: full admin link set
 *
 * Shows the user's email + "Cerrar sesión" button when authenticated.
 * All styles use Tailwind v4 utility classes — zero inline style props.
 */

import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useLogout } from '@/shared/hooks/useLogout'
import { useNavLinks } from '@/shared/hooks/useNavLinks'

export default function Navbar() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const { logout, isLoading } = useLogout()
  const navLinks = useNavLinks()

  return (
    <nav className="bg-gray-900 text-white flex items-center justify-between px-6 py-3">
      {/* Brand */}
      <Link to="/" className="font-bold text-lg text-white no-underline shrink-0">
        Food Store
      </Link>

      {/* Dynamic nav links + auth section */}
      <div className="flex items-center gap-4 flex-wrap">
        {navLinks.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className="text-gray-300 hover:text-white text-sm transition-colors"
          >
            {link.label}
          </Link>
        ))}

        {isAuthenticated && (
          <>
            <span className="text-gray-400 text-sm select-none">
              {user?.email ?? user?.name}
            </span>

            <button
              onClick={logout}
              disabled={isLoading}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:bg-gray-500 disabled:cursor-not-allowed text-white text-sm font-medium rounded transition-colors"
              aria-busy={isLoading}
              aria-label="Cerrar sesión"
            >
              {isLoading ? 'Saliendo...' : 'Cerrar sesión'}
            </button>
          </>
        )}
      </div>
    </nav>
  )
}
