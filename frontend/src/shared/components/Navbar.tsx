/**
 * Navbar — top navigation bar with conditional logout button.
 *
 * Renders a "Logout" button when the user is authenticated.
 * The button is disabled while the logout request is in flight
 * to prevent double-submission (task 5.3).
 *
 * Uses the `useLogout` hook which:
 *  1. Calls POST /api/v1/auth/logout (best-effort server-side revocation)
 *  2. Always clears local auth state in `finally` regardless of backend outcome
 */

import { Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useLogout } from '../hooks/useLogout'

export default function Navbar() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const { logout, isLoading } = useLogout()

  return (
    <nav
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1.5rem',
        backgroundColor: '#1f2937',
        color: '#f9fafb',
      }}
    >
      {/* Brand */}
      <Link
        to="/"
        style={{ color: '#f9fafb', textDecoration: 'none', fontWeight: 700, fontSize: '1.125rem' }}
      >
        Food Store
      </Link>

      {/* Navigation links */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <Link to="/catalog" style={{ color: '#d1d5db', textDecoration: 'none' }}>
          Catalog
        </Link>

        {isAuthenticated ? (
          <>
            <Link to="/profile" style={{ color: '#d1d5db', textDecoration: 'none' }}>
              {user?.email ?? 'Profile'}
            </Link>

            {/* Logout button — disabled while request is in flight (task 5.3) */}
            <button
              onClick={logout}
              disabled={isLoading}
              style={{
                padding: '0.375rem 0.875rem',
                backgroundColor: isLoading ? '#6b7280' : '#dc2626',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '0.875rem',
                fontWeight: 500,
                transition: 'background-color 0.15s ease',
              }}
              aria-busy={isLoading}
              aria-label="Logout"
            >
              {isLoading ? 'Logging out...' : 'Logout'}
            </button>
          </>
        ) : (
          <>
            <Link to="/login" style={{ color: '#d1d5db', textDecoration: 'none' }}>
              Login
            </Link>
            <Link to="/register" style={{ color: '#d1d5db', textDecoration: 'none' }}>
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  )
}
