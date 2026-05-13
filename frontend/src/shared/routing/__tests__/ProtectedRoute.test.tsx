/**
 * ProtectedRoute Tests
 *
 * Covers all guard scenarios:
 * - Hydration pending → show loading, no redirect
 * - Not authenticated → redirect to /login
 * - Authenticated but missing role → redirect to /403
 * - Authenticated with required role → render Outlet content
 * - Authenticated, no requiredRoles → render Outlet content
 *
 * Strategy:
 * - Mock useAuthStore with vi.mock so we control store state per test
 * - Wrap in MemoryRouter to avoid needing a full BrowserRouter
 * - Use Routes + Route with ProtectedRoute as the layout route,
 *   and a child route rendering a sentinel <div> to verify Outlet renders
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '../ProtectedRoute'

// ── Mock useAuthStore ─────────────────────────────────────────────────────────
// We mock the entire module and control the return value per test via mockReturnValue.
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

// Import AFTER vi.mock so we get the mocked version
import { useAuthStore } from '@/store/authStore'
const mockUseAuthStore = useAuthStore as unknown as ReturnType<typeof vi.fn>

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Build a minimal authStore state for use in tests.
 */
function makeAuthState(overrides: {
  _hasHydrated?: boolean
  isAuthenticated?: boolean
  roles?: string[]
}) {
  const roles = overrides.roles ?? []
  return (selector: (state: {
    _hasHydrated: boolean
    isAuthenticated: boolean
    hasRole: (role: string) => boolean
  }) => unknown) =>
    selector({
      _hasHydrated: overrides._hasHydrated ?? true,
      isAuthenticated: overrides.isAuthenticated ?? false,
      hasRole: (role: string) => roles.includes(role),
    })
}

/**
 * Render ProtectedRoute as a layout route inside a MemoryRouter.
 *
 * - `initialPath`: the route the "browser" starts on
 * - `requiredRoles`: passed to ProtectedRoute
 * - child at `/protected` renders <div data-testid="outlet-content" />
 * - `/login` renders <div data-testid="login-page" />
 * - `/403` renders <div data-testid="forbidden-page" />
 */
function renderProtectedRoute(
  initialPath: string,
  requiredRoles?: string[]
) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        {/* Sentinel destinations so Navigate can resolve */}
        <Route path="/login" element={<div data-testid="login-page" />} />
        <Route path="/403" element={<div data-testid="forbidden-page" />} />

        {/* Layout route under test */}
        <Route element={<ProtectedRoute requiredRoles={requiredRoles} />}>
          <Route path="/protected" element={<div data-testid="outlet-content" />} />
        </Route>
      </Routes>
    </MemoryRouter>
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── Task 4.2 ────────────────────────────────────────────────────────────────
  it('4.2 shows loading indicator when _hasHydrated is false (no redirect)', () => {
    mockUseAuthStore.mockImplementation(
      makeAuthState({ _hasHydrated: false, isAuthenticated: false })
    )

    renderProtectedRoute('/protected')

    // Loading spinner should be present
    expect(screen.getByRole('status')).toBeInTheDocument()
    // Neither redirect target should be rendered
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument()
    expect(screen.queryByTestId('forbidden-page')).not.toBeInTheDocument()
    expect(screen.queryByTestId('outlet-content')).not.toBeInTheDocument()
  })

  // ── Task 4.3 ────────────────────────────────────────────────────────────────
  it('4.3 redirects to /login when not authenticated (_hasHydrated = true)', () => {
    mockUseAuthStore.mockImplementation(
      makeAuthState({ _hasHydrated: true, isAuthenticated: false })
    )

    renderProtectedRoute('/protected')

    expect(screen.getByTestId('login-page')).toBeInTheDocument()
    expect(screen.queryByTestId('outlet-content')).not.toBeInTheDocument()
  })

  // ── Task 4.4 ────────────────────────────────────────────────────────────────
  it('4.4 redirects to /403 when authenticated but missing required role', () => {
    mockUseAuthStore.mockImplementation(
      makeAuthState({
        _hasHydrated: true,
        isAuthenticated: true,
        roles: ['CLIENT'], // does NOT have ADMIN
      })
    )

    renderProtectedRoute('/protected', ['ADMIN'])

    expect(screen.getByTestId('forbidden-page')).toBeInTheDocument()
    expect(screen.queryByTestId('outlet-content')).not.toBeInTheDocument()
  })

  // ── Task 4.5 ────────────────────────────────────────────────────────────────
  it('4.5 renders Outlet when authenticated with at least one required role', () => {
    mockUseAuthStore.mockImplementation(
      makeAuthState({
        _hasHydrated: true,
        isAuthenticated: true,
        roles: ['ADMIN'], // satisfies ['CLIENT', 'ADMIN'] via some()
      })
    )

    renderProtectedRoute('/protected', ['CLIENT', 'ADMIN'])

    expect(screen.getByTestId('outlet-content')).toBeInTheDocument()
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument()
    expect(screen.queryByTestId('forbidden-page')).not.toBeInTheDocument()
  })

  // ── Task 4.6 ────────────────────────────────────────────────────────────────
  it('4.6 renders Outlet when authenticated and no requiredRoles defined', () => {
    mockUseAuthStore.mockImplementation(
      makeAuthState({
        _hasHydrated: true,
        isAuthenticated: true,
        roles: [],
      })
    )

    // No requiredRoles — auth-only route
    renderProtectedRoute('/protected', undefined)

    expect(screen.getByTestId('outlet-content')).toBeInTheDocument()
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument()
    expect(screen.queryByTestId('forbidden-page')).not.toBeInTheDocument()
  })
})
