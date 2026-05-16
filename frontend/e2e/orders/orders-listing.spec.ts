/**
 * E2E tests for orders listing pages.
 *
 * Uses loginAs() helper (addInitScript) to seed Zustand auth state before hydration.
 * Mocks backend via page.route() — no real FastAPI needed.
 *
 * Patterns from testing-e2e-playwright skill:
 * - addInitScript for localStorage seed (CRITICAL: before React hydrates)
 * - page.route() to mock GET /api/v1/pedidos
 * - Wait for hydration before assertions
 * - Role-based access guard verification
 */

import { test, expect } from '@playwright/test'
import { loginAs, logout } from '../helpers/auth'

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const mockOrders = [
  {
    id: 1,
    usuario_id: 2,
    estado_pedido_id: 1,   // PENDIENTE
    total: 1200.0,
    creado_en: '2026-05-10T14:30:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
  },
  {
    id: 2,
    usuario_id: 2,
    estado_pedido_id: 5,   // ENTREGADO
    total: 850.5,
    creado_en: '2026-05-12T09:00:00Z',
    observacion: 'Sin cebolla',
    direccion_snapshot: null,
    forma_pago_id: 2,
  },
]

const mockOrdersPage = {
  items: mockOrders,
  total: 2,
  limit: 10,
  offset: 0,
}

const emptyOrdersPage = {
  items: [],
  total: 0,
  limit: 10,
  offset: 0,
}

// ---------------------------------------------------------------------------
// Helper: mock the orders endpoint
// ---------------------------------------------------------------------------

async function mockOrdersEndpoint(
  page: import('@playwright/test').Page,
  body = mockOrdersPage,
) {
  await page.route('**/api/v1/pedidos**', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(body),
    })
  })
}

// ---------------------------------------------------------------------------
// MyOrdersPage — CLIENT view (/mis-pedidos)
// ---------------------------------------------------------------------------

test.describe('/mis-pedidos — CLIENT view', () => {
  test('CLIENT can access /mis-pedidos and sees order cards', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await mockOrdersEndpoint(page)
    await page.goto('/mis-pedidos')

    // Wait for hydration
    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })

    // Verify at least one order card is visible
    await expect(page.getByLabelText('Pedido #1')).toBeVisible({ timeout: 5000 })
    await expect(page.getByLabelText('Pedido #2')).toBeVisible({ timeout: 5000 })
  })

  test('CLIENT sees empty state when no orders', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await mockOrdersEndpoint(page, emptyOrdersPage)
    await page.goto('/mis-pedidos')

    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })

    await expect(
      page.getByText('No tenés pedidos todavía.'),
    ).toBeVisible({ timeout: 5000 })

    // Catalog link is present
    await expect(page.getByRole('link', { name: 'Ir al catálogo' })).toBeVisible()
  })

  test('unauthenticated user is redirected to /login', async ({ page }) => {
    await logout(page)
    await page.goto('/mis-pedidos')
    await expect(page).toHaveURL(/\/login/)
  })
})

// ---------------------------------------------------------------------------
// OrdersPanelPage — ADMIN/PEDIDOS view (/admin/pedidos)
// ---------------------------------------------------------------------------

test.describe('/admin/pedidos — ADMIN panel', () => {
  test('ADMIN can access /admin/pedidos and sees the orders table', async ({ page }) => {
    await loginAs(page, 'ADMIN')
    await mockOrdersEndpoint(page)
    await page.goto('/admin/pedidos')

    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })

    // The table with role="table" must be present
    await expect(
      page.getByRole('table', { name: 'Tabla de pedidos' }),
    ).toBeVisible({ timeout: 5000 })
  })

  test('PEDIDOS role can access /admin/pedidos', async ({ page }) => {
    await loginAs(page, 'PEDIDOS')
    await mockOrdersEndpoint(page)
    await page.goto('/admin/pedidos')

    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })

    await expect(page).not.toHaveURL(/\/403/)
    await expect(page).not.toHaveURL(/\/login/)
  })

  test('CLIENT role is redirected to /403 when accessing /admin/pedidos', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.goto('/admin/pedidos')

    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })

    await expect(page).toHaveURL(/\/403/)
  })

  test('filter by estado sends correct query param to API', async ({ page }) => {
    await loginAs(page, 'ADMIN')

    // Track request URLs to verify query params
    const requestUrls: string[] = []
    await page.route('**/api/v1/pedidos**', (route) => {
      requestUrls.push(route.request().url())
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockOrdersPage),
      })
    })

    await page.goto('/admin/pedidos')

    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })

    // Select "Pendiente" (id=1) from the estado filter
    await page.selectOption('#filter-estado', '1')

    // Wait for the filtered request
    await page.waitForTimeout(300)

    // At least one request should have estado_pedido_id=1 in the URL
    const filteredRequest = requestUrls.find((url) =>
      url.includes('estado_pedido_id=1'),
    )
    expect(filteredRequest).toBeTruthy()
  })

  test('pagination sends correct offset to API', async ({ page }) => {
    await loginAs(page, 'ADMIN')

    // Return enough data to show pagination (total > LIMIT)
    const bigPage = { ...mockOrdersPage, total: 30 }

    const requestUrls: string[] = []
    await page.route('**/api/v1/pedidos**', (route) => {
      requestUrls.push(route.request().url())
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(bigPage),
      })
    })

    await page.goto('/admin/pedidos')

    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })

    // Wait for initial render
    await page.waitForTimeout(300)

    // Click page 2
    await page.getByLabel('Página 2').click()

    await page.waitForTimeout(300)

    // Verify a request with offset=15 was sent (LIMIT=15)
    const page2Request = requestUrls.find((url) => url.includes('offset=15'))
    expect(page2Request).toBeTruthy()
  })
})
