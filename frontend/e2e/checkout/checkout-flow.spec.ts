/**
 * E2E tests: checkout flow authentication and access control.
 *
 * 8.2 — Redirect to /login when not authenticated
 * 8.3 — Redirect to / with toast when cart is empty (authenticated)
 * 8.8 — Form validation: nombre_comprador vacío → error visible, POST /pedidos NOT called
 */

import { test, expect } from '@playwright/test'
import { loginAs, logout } from '../helpers/auth'

// ---------------------------------------------------------------------------
// Helper: seed a cart with items in localStorage
// ---------------------------------------------------------------------------
async function seedCart(page: Parameters<typeof page.addInitScript>[0] extends (fn: infer F) => unknown ? never : Parameters<typeof loginAs>[0]) {
  await page.addInitScript(() => {
    localStorage.setItem(
      'food-store-cart',
      JSON.stringify({
        state: {
          items: [
            {
              productId: '1',
              name: 'Hamburguesa Clásica',
              price: 1500,
              precio_carrito: 1500,
              quantity: 2,
            },
          ],
        },
        version: 0,
      }),
    )
  })
}

async function clearCart(page: Parameters<typeof loginAs>[0]) {
  await page.addInitScript(() => {
    localStorage.setItem(
      'food-store-cart',
      JSON.stringify({ state: { items: [] }, version: 0 }),
    )
  })
}

test.describe('Checkout Flow — Auth & Access', () => {
  // 8.2 — Without auth → redirect to /login
  test('navigating to /checkout without auth redirects to /login', async ({
    page,
  }) => {
    await logout(page)
    await page.goto('/checkout')
    await expect(page).toHaveURL('/login')
  })

  // 8.3 — Authenticated with empty cart → redirect to /
  test('authenticated with empty cart redirects to /', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await clearCart(page)

    // Mock the cart validation endpoint to return empty cart
    await page.route('**/api/v1/pedidos/validar', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          stock_insuficiente: [],
          productos_invalidos: [],
          cambios_de_precio: [],
          carrito_vacio: true,
          sin_direccion: false,
        }),
      })
    })

    await page.goto('/checkout')

    // Should redirect to home
    await expect(page).toHaveURL('/')
  })
})

test.describe('Checkout Flow — Form Validation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page)

    // Mock validation as clean
    await page.route('**/api/v1/pedidos/validar', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          stock_insuficiente: [],
          productos_invalidos: [],
          cambios_de_precio: [],
          carrito_vacio: false,
          sin_direccion: false,
        }),
      })
    })
  })

  // 8.8 — Empty nombre → error visible, POST /pedidos not called
  test('empty nombre_comprador shows error and does not call POST /pedidos', async ({
    page,
  }) => {
    let pedidosPostCalled = false

    await page.route('**/api/v1/pedidos', (route) => {
      if (route.request().method() === 'POST') {
        pedidosPostCalled = true
        route.abort()
      } else {
        route.continue()
      }
    })

    await page.goto('/checkout')

    // Wait for the checkout form to appear
    await page.waitForSelector('input#nombre_comprador', { timeout: 5000 })

    // Select MercadoPago
    await page.click('[data-testid="payment-method-mercadopago"]')

    // Click "Preparar pago" without filling the form
    const prepBtn = page.getByTestId('generate-preference-btn')
    if (await prepBtn.isVisible()) {
      await prepBtn.click()
    }

    // Check that the error message is visible
    await expect(page.locator('#nombre-error')).toBeVisible()
    await expect(page.locator('text=El nombre es obligatorio')).toBeVisible()

    // Verify POST /pedidos was NOT called
    expect(pedidosPostCalled).toBe(false)
  })
})
