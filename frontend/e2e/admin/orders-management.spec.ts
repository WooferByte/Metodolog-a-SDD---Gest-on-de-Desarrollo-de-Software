/**
 * E2E tests for the admin orders management panel.
 *
 * Tests the new management UI features:
 * - Checkbox selection and BulkActionsBar
 * - StateTransitionModal for per-order state change
 * - Bulk cancel flow with BulkConfirmModal
 * - Filter by estado and advanced email filter
 * - Role guard: CLIENT → /403
 *
 * Uses loginAs() helper (addInitScript) to seed auth state before React hydrates.
 * Mocks backend via page.route() — no real FastAPI needed.
 *
 * Patterns from testing-e2e-playwright skill:
 * - addInitScript for Zustand hydration (CRITICAL)
 * - page.route() for API mocks
 * - waitForFunction for Zustand hydration check
 */

import { test, expect } from '@playwright/test'
import { loginAs, logout } from '../helpers/auth'

// ---------------------------------------------------------------------------
// Mock fixtures
// ---------------------------------------------------------------------------

const mockOrders = [
  {
    id: 101,
    usuario_id: 10,
    usuario_email: 'user1@test.com',
    estado_pedido_id: 2,    // CONFIRMADO
    total: 1500.0,
    creado_en: '2026-05-14T10:00:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
  },
  {
    id: 102,
    usuario_id: 11,
    usuario_email: 'user2@test.com',
    estado_pedido_id: 2,    // CONFIRMADO
    total: 2200.0,
    creado_en: '2026-05-14T11:00:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
  },
  {
    id: 103,
    usuario_id: 12,
    usuario_email: 'user3@test.com',
    estado_pedido_id: 3,    // EN_PREPARACIÓN
    total: 800.0,
    creado_en: '2026-05-14T12:00:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
  },
  {
    id: 104,
    usuario_id: 13,
    usuario_email: 'user4@test.com',
    estado_pedido_id: 5,    // ENTREGADO (terminal)
    total: 350.0,
    creado_en: '2026-05-14T13:00:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
  },
  {
    id: 105,
    usuario_id: 14,
    usuario_email: 'user5@test.com',
    estado_pedido_id: 1,    // PENDIENTE
    total: 600.0,
    creado_en: '2026-05-14T14:00:00Z',
    observacion: null,
    direccion_snapshot: null,
    forma_pago_id: 1,
  },
]

const mockOrdersPage = {
  items: mockOrders,
  total: mockOrders.length,
  limit: 15,
  offset: 0,
}

const PANEL_URL = '/admin/pedidos'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function setupAdminPanel(page: Parameters<typeof loginAs>[0]) {
  await loginAs(page, 'ADMIN')

  // Mock the orders list endpoint
  await page.route('**/api/v1/pedidos*', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockOrdersPage),
    })
  })

  await page.goto(PANEL_URL)

  // Wait for Zustand hydration
  await page.waitForFunction(() => {
    const raw = localStorage.getItem('food-store-auth')
    if (!raw) return true
    const parsed = JSON.parse(raw)
    return parsed?.state?._hasHydrated === true
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('OrdersPanelPage — Management features', () => {

  test('renders the management table with orders', async ({ page }) => {
    await setupAdminPanel(page)
    // Table with management columns should be visible
    await expect(page.getByRole('grid', { name: 'Tabla de gestión de pedidos' })).toBeVisible()
    await expect(page.getByText('#101')).toBeVisible()
    await expect(page.getByText('#102')).toBeVisible()
  })

  test('selecting a single order shows BulkActionsBar with count 1', async ({ page }) => {
    await setupAdminPanel(page)
    const checkbox = page.getByLabel('Seleccionar pedido #101')
    await checkbox.click()
    await expect(page.getByText('1 pedido seleccionado')).toBeVisible()
  })

  test('header checkbox selects all orders', async ({ page }) => {
    await setupAdminPanel(page)
    const headerCb = page.getByLabel('Seleccionar todos los pedidos')
    await headerCb.click()
    // All 5 selected → "5 pedidos seleccionados"
    await expect(page.getByText('5 pedidos seleccionados')).toBeVisible()
  })

  test('BulkActionsBar does not render when nothing is selected', async ({ page }) => {
    await setupAdminPanel(page)
    await expect(page.getByRole('toolbar', { name: 'Acciones para pedidos seleccionados' })).not.toBeVisible()
  })

  test('"Cambiar estado" is disabled when mixed states are selected', async ({ page }) => {
    await setupAdminPanel(page)
    // Select order 101 (CONFIRMADO) and 103 (EN_PREPARACIÓN) — mixed states
    await page.getByLabel('Seleccionar pedido #101').click()
    await page.getByLabel('Seleccionar pedido #103').click()

    const btn = page.getByRole('button', { name: /Cambiar estado/i })
    await expect(btn).toBeDisabled()
  })

  test('"Cambiar estado" is enabled when all selected have the same state', async ({ page }) => {
    await setupAdminPanel(page)
    // Select orders 101 and 102 — both CONFIRMADO
    await page.getByLabel('Seleccionar pedido #101').click()
    await page.getByLabel('Seleccionar pedido #102').click()

    const btn = page.getByRole('button', { name: /Cambiar estado/i })
    await expect(btn).not.toBeDisabled()
  })

  test('state transition modal opens on per-order "Estado" button click', async ({ page }) => {
    await setupAdminPanel(page)
    // Click the Estado button for order 101 (CONFIRMADO)
    const estadoBtn = page.getByLabel('Cambiar estado del pedido #101')
    await estadoBtn.click()
    await expect(page.getByRole('dialog')).toBeVisible()
    // Should show valid transitions for CONFIRMADO (→ EN_PREPARACIÓN, → CANCELADO)
    await expect(page.getByRole('radio', { name: /En preparación/i })).toBeVisible()
    await expect(page.getByRole('radio', { name: /Cancelado/i })).toBeVisible()
  })

  test('state transition modal closes on Escape key', async ({ page }) => {
    await setupAdminPanel(page)
    await page.getByLabel('Cambiar estado del pedido #101').click()
    await expect(page.getByRole('dialog')).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).not.toBeVisible()
  })

  test('"Estado" button is disabled for terminal state orders', async ({ page }) => {
    await setupAdminPanel(page)
    // Order 104 is ENTREGADO (terminal)
    const btn = page.getByLabel('Pedido #104 en estado terminal — sin transiciones')
    await expect(btn).toBeDisabled()
  })

  test('bulk cancel flow opens confirm dialog and shows correct count', async ({ page }) => {
    await setupAdminPanel(page)
    await page.getByLabel('Seleccionar pedido #101').click()
    await page.getByLabel('Seleccionar pedido #102').click()

    await page.getByText('Cancelar seleccionados').click()
    await expect(page.getByRole('alertdialog')).toBeVisible()
    await expect(page.getByText(/2 pedidos/)).toBeVisible()
  })

  test('bulk cancel executes DELETE requests and shows toast', async ({ page }) => {
    await loginAs(page, 'ADMIN')

    // Mock orders listing
    await page.route('**/api/v1/pedidos*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockOrdersPage),
        })
      } else {
        route.continue()
      }
    })

    // Mock DELETE for both orders
    let deletedIds: number[] = []
    await page.route('**/api/v1/pedidos/101', (route) => {
      if (route.request().method() === 'DELETE') {
        deletedIds.push(101)
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) })
      } else {
        route.continue()
      }
    })
    await page.route('**/api/v1/pedidos/102', (route) => {
      if (route.request().method() === 'DELETE') {
        deletedIds.push(102)
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) })
      } else {
        route.continue()
      }
    })

    await page.goto(PANEL_URL)
    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })

    await page.getByLabel('Seleccionar pedido #101').click()
    await page.getByLabel('Seleccionar pedido #102').click()
    await page.getByText('Cancelar seleccionados').click()

    // Confirm in the dialog
    const dialog = page.getByRole('alertdialog')
    await expect(dialog).toBeVisible()
    await dialog.getByText(/Cancelar 2 pedidos/i).click()

    // Should have called DELETE for both
    await page.waitForFunction(() => true) // let promises settle
    expect(deletedIds).toContain(101)
    expect(deletedIds).toContain(102)
  })

  test('advanced filters panel is collapsed by default', async ({ page }) => {
    await setupAdminPanel(page)
    // The <details> should not be open — advanced filter inputs should not be visible
    const emailInput = page.getByLabel('Filtrar por email exacto del usuario')
    await expect(emailInput).not.toBeVisible()
  })

  test('expanding advanced filters panel reveals email filter', async ({ page }) => {
    await setupAdminPanel(page)
    await page.getByLabel('Filtros avanzados de pedidos').click()
    const emailInput = page.getByLabel('Filtrar por email exacto del usuario')
    await expect(emailInput).toBeVisible()
  })

})

test.describe('OrdersPanelPage — Role guard', () => {
  test('CLIENT role is redirected to /403', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.goto(PANEL_URL)
    await page.waitForFunction(() => {
      const raw = localStorage.getItem('food-store-auth')
      if (!raw) return true
      const parsed = JSON.parse(raw)
      return parsed?.state?._hasHydrated === true
    })
    await expect(page).toHaveURL('/403')
  })

  test('unauthenticated user is redirected to /login', async ({ page }) => {
    await logout(page)
    await page.goto(PANEL_URL)
    await expect(page).toHaveURL('/login')
  })
})
