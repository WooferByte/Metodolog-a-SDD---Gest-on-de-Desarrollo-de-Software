import { Page } from '@playwright/test'

export type Role = 'ADMIN' | 'CLIENT' | 'STOCK' | 'PEDIDOS'

const USERS: Record<Role, { id: number; email: string }> = {
  ADMIN:   { id: 1, email: 'admin@foodstore.com' },
  CLIENT:  { id: 2, email: 'cliente@test.com' },
  STOCK:   { id: 3, email: 'stock@test.com' },
  PEDIDOS: { id: 4, email: 'pedidos@test.com' },
}

/**
 * Seedea el authStore de Zustand en localStorage ANTES de que React hidrate.
 * Usar siempre con addInitScript — nunca con page.evaluate post-navigate.
 */
export async function loginAs(page: Page, role: Role, token = 'e2e-test-token') {
  const user = USERS[role]
  await page.addInitScript(({ key, value }) => {
    localStorage.setItem(key, JSON.stringify(value))
  }, {
    key: 'food-store-auth',
    value: {
      state: {
        isAuthenticated: true,
        accessToken: token,
        user: { id: user.id, email: user.email, roles: [role] },
        _hasHydrated: true,
      },
      version: 0,
    },
  })
}

/**
 * Limpia el authStore — simula usuario no autenticado.
 */
export async function logout(page: Page) {
  await page.addInitScript(() => {
    localStorage.removeItem('food-store-auth')
  })
}

/**
 * Espera a que Zustand termine de rehydratar antes de hacer assertions.
 * Necesario cuando ProtectedRoute depende de _hasHydrated.
 */
export async function waitForHydration(page: Page) {
  await page.waitForFunction(() => {
    const raw = localStorage.getItem('food-store-auth')
    if (!raw) return true
    try {
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    } catch {
      return true
    }
  })
}
