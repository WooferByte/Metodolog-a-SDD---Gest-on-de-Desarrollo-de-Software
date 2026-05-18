/**
 * E2E tests: MercadoPago payment simulation.
 *
 * 8.6 — Simulating successful payment: navigate to /checkout?payment=success&pedido_id=99
 *        → verify success modal is visible with "Ver mi pedido" button
 *
 * 8.7 — Simulating failed payment: navigate to /checkout?payment=failure&pedido_id=99
 *        → verify error modal is visible with "Intentar de nuevo" button
 */

import { test, expect } from '@playwright/test'
import { loginAs } from '../helpers/auth'

test.beforeEach(async ({ page }) => {
  await loginAs(page, 'CLIENT')

  // Seed cart with items (so redirect-to-home check doesn't fire)
  await page.addInitScript(() => {
    localStorage.setItem(
      'food-store-cart',
      JSON.stringify({
        state: {
          items: [
            {
              productId: '1',
              name: 'Hamburguesa',
              price: 1500,
              precio_carrito: 1500,
              quantity: 1,
            },
          ],
        },
        version: 0,
      }),
    )
  })

  // Mock validation endpoint
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

  // Mock pedidos POST
  await page.route('**/api/v1/pedidos', (route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 99, total: '1500.00' }),
      })
    } else {
      route.continue()
    }
  })

  // Mock crear-preferencia
  await page.route('**/api/v1/pagos/crear-preferencia', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        preference_id: 'pref_test_123',
        pago_id: 1,
        init_point: 'https://www.mercadopago.com.ar/checkout/v1/redirect',
      }),
    }),
  )
})

test.describe('MercadoPago Payment Simulation', () => {
  // 8.6 — Successful payment via query params
  test('navigating to /checkout?payment=success&pedido_id=99 shows success modal', async ({
    page,
  }) => {
    await page.goto('/checkout?payment=success&pedido_id=99')

    // Wait for the modal to appear
    await expect(
      page.getByTestId('payment-status-modal'),
    ).toBeVisible({ timeout: 5000 })

    // Check success content
    await expect(page.getByText('¡Pago exitoso!')).toBeVisible()
    await expect(page.getByTestId('modal-view-order-btn')).toBeVisible()
  })

  test('success modal shows pedido_id in message', async ({ page }) => {
    await page.goto('/checkout?payment=success&pedido_id=99')

    await expect(page.getByTestId('payment-status-modal')).toBeVisible({
      timeout: 5000,
    })
    await expect(page.getByText(/pedido #99/i)).toBeVisible()
  })

  // 8.7 — Failed payment via query params
  test('navigating to /checkout?payment=failure&pedido_id=99 shows error modal', async ({
    page,
  }) => {
    await page.goto('/checkout?payment=failure&pedido_id=99')

    // Wait for the modal to appear
    await expect(
      page.getByTestId('payment-status-modal'),
    ).toBeVisible({ timeout: 5000 })

    // Check error content
    await expect(
      page.getByText('El pago no pudo procesarse'),
    ).toBeVisible()
    await expect(page.getByTestId('modal-retry-btn')).toBeVisible()
  })

  test('error modal has "Intentar de nuevo" and "Cancelar" buttons', async ({
    page,
  }) => {
    await page.goto('/checkout?payment=failure&pedido_id=99')

    await expect(page.getByTestId('payment-status-modal')).toBeVisible({
      timeout: 5000,
    })
    await expect(page.getByTestId('modal-retry-btn')).toBeVisible()
    await expect(page.getByTestId('modal-cancel-btn')).toBeVisible()
  })

  // Pending payment
  test('navigating to /checkout?payment=pending shows pending modal', async ({
    page,
  }) => {
    await page.goto('/checkout?payment=pending&pedido_id=99')

    await expect(
      page.getByTestId('payment-status-modal'),
    ).toBeVisible({ timeout: 5000 })

    await expect(page.getByText('Pago en proceso')).toBeVisible()
    await expect(page.getByTestId('modal-view-orders-btn')).toBeVisible()
  })
})
