import { Page } from '@playwright/test'

/**
 * Role types matching the RBAC seed data in the backend.
 * IDs match: ADMIN(1) STOCK(2) PEDIDOS(3) CLIENT(4)
 */
type Role = 'ADMIN' | 'CLIENT' | 'STOCK' | 'PEDIDOS'

const USERS: Record<Role, { id: number; email: string; name: string }> = {
  ADMIN:   { id: 1, email: 'admin@foodstore.com',    name: 'Admin User' },
  CLIENT:  { id: 2, email: 'cliente@test.com',       name: 'Cliente Test' },
  STOCK:   { id: 3, email: 'stock@test.com',         name: 'Stock User' },
  PEDIDOS: { id: 4, email: 'pedidos@test.com',       name: 'Pedidos User' },
}

/**
 * loginAs — seed auth state in localStorage before React hydrates.
 *
 * Uses addInitScript (runs before page load) so Zustand reads the correct state
 * from localStorage on first render. Never use page.evaluate after navigation.
 *
 * localStorage key: 'food-store-auth' (matches authStore persist name)
 * Structure: { state: { accessToken, user, isAuthenticated, _hasHydrated }, version: 0 }
 *
 * @param page - Playwright Page instance
 * @param role - Role to authenticate as
 * @param token - JWT access token (fake for tests)
 */
export async function loginAs(page: Page, role: Role, token = 'test-token') {
  const user = USERS[role]
  await page.addInitScript(({ key, value }) => {
    localStorage.setItem(key, JSON.stringify(value))
  }, {
    key: 'food-store-auth',
    value: {
      state: {
        isAuthenticated: true,
        accessToken: token,
        refreshToken: null,
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          roles: [role],
        },
        _hasHydrated: true,
      },
      version: 0,
    },
  })
}

/**
 * logout — clear auth state in localStorage before React hydrates.
 *
 * @param page - Playwright Page instance
 */
export async function logout(page: Page) {
  await page.addInitScript(() => {
    localStorage.removeItem('food-store-auth')
  })
}
