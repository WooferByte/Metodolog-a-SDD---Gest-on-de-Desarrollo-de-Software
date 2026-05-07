/**
 * Example: AuthStore Usage
 * 
 * Demonstrates how to use the authStore to manage user authentication,
 * token updates, and role-based access.
 */

import { useAuthStore } from '@/store'

/**
 * UserProfile Component
 * 
 * Shows how to:
 * - Access authentication state with selectors
 * - Use the hasRole helper method
 * - Display user information
 * - Handle logout
 */
export function UserProfileExample() {
  // Selector pattern: Only re-render when these specific values change
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const hasRole = useAuthStore((state) => state.hasRole)

  if (!isAuthenticated || !user) {
    return <div>Not authenticated. Please login.</div>
  }

  return (
    <div>
      <h2>User Profile</h2>
      <p>Name: {user.name}</p>
      <p>Email: {user.email}</p>
      <p>Roles: {user.roles.join(', ')}</p>

      {hasRole('admin') && <p>You have admin access</p>}

      <button onClick={logout}>Logout</button>
    </div>
  )
}

/**
 * TokenUpdater Component
 * 
 * Shows how to:
 * - Update JWT tokens
 * - Update user data
 * - Handle authentication state changes
 */
export function TokenUpdaterExample() {
  const updateTokens = useAuthStore((state) => state.updateTokens)
  const setUser = useAuthStore((state) => state.setUser)

  const handleLogin = () => {
    // After successful API login, store tokens
    updateTokens('access-token-jwt-xyz', 'refresh-token-xyz')

    // Store user info
    setUser({
      id: 'user-123',
      email: 'user@example.com',
      name: 'John Doe',
      roles: ['customer'],
    })
  }

  return (
    <div>
      <button onClick={handleLogin}>Login</button>
    </div>
  )
}
