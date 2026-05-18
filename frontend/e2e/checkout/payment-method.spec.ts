/**
 * E2E tests: payment method selection.
 *
 * 8.4 — Authenticated with cart → select "MercadoPago" → pay button enables
 * 8.5 — Select disabled method "Tarjeta" → method does NOT change
 */

import { test, expect } from '@playwright/test'
import { loginAs } from '../helpers/auth'

test.beforeEach(async ({ page }) => {
  await loginAs(page, 'CLIENT')

  // Seed cart
  await page.addInitScript(() => {
    localStorage.setItem(
      'food-store-cart',
      JSON.stringify({
        state: {
          items: [
            {
              productId: '1',
              name: 'Pizza',
              price: 2000,
              precio_carrito: 2000,
              quantity: 1,
            },
          ],
        },
        version: 0,
      }),
    )
  })

  // Mock validation as clean
  await page.route('**/api/v1/pedidos/validar', (route) =>
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
    }),
  )
})

test.describe('Payment Method Selection', () => {
  // 8.4 — Select MercadoPago → button appears
  test('selecting MercadoPago shows the payment button', async ({ page }) => {
    await page.goto('/checkout')
    await page.waitForSelector('[data-testid="payment-method-mercadopago"]', {
      timeout: 5000,
    })

    await page.click('[data-testid="payment-method-mercadopago"]')

    // The MercadoPago button should be visible after selecting the method
    await expect(
      page.locator('[data-testid="mercadopago-button"], [data-testid="generate-preference-btn"]'),
    ).toBeVisible({ timeout: 3000 })
  })

  // 8.5 — Click disabled "Tarjeta" → method does not change
  test('clicking disabled Tarjeta method does not change the selection', async ({
    page,
  }) => {
    await page.goto('/checkout')
    await page.waitForSelector('[data-testid="payment-method-card"]', {
      timeout: 5000,
    })

    // Click MercadoPago first to set a known state
    await page.click('[data-testid="payment-method-mercadopago"]')
    const mpBefore = page.getByTestId('payment-method-mercadopago')
    await expect(mpBefore).toHaveAttribute('aria-checked', 'true')

    // Click disabled Tarjeta option
    await page.click('[data-testid="payment-method-card"]')

    // MercadoPago should still be selected (Tarjeta is disabled)
    await expect(mpBefore).toHaveAttribute('aria-checked', 'true')
    await expect(
      page.getByTestId('payment-method-card'),
    ).toHaveAttribute('aria-checked', 'false')
  })
})
