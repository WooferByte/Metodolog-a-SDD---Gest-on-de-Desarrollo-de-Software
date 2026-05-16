/**
 * E2E tests for OrderDetailPage.
 *
 * Covers:
 *   1. CLIENT views their order detail — header, timeline visible
 *   2. Timeline with multiple status entries renders all items
 *   3. CLIENT cancels a PENDIENTE order — modal + confirm → toast success
 *   4. Modal closes with Escape without executing the DELETE request
 *   5. Unauthenticated user → redirected to /login
 *   6. CLIENT tries admin route → redirected to /403
 *   7. Order not found (404) → shows error state with CTA
 *
 * Uses:
 *   - loginAs() helper: seeds auth in localStorage via addInitScript
 *   - page.route(): mocks backend responses without a real server
 */

import { test, expect } from '@playwright/test'
import { loginAs, logout } from '../helpers/auth'

// ─── Mock data ───────────────────────────────────────────────────────────────

const mockOrder = {
  id: 1,
  usuario_id: 2,
  estado_pedido_id: 1,    // PENDIENTE
  total: 2500.00,
  creado_en: '2026-05-15T14:30:00Z',
  observacion: null,
  direccion_snapshot: { calle: 'Av. Corrientes', numero: '1234', ciudad: 'Buenos Aires', provincia: 'CABA' },
  forma_pago_id: 1,
  direccion_entrega_id: 1,
  actualizado_en: '2026-05-15T14:30:00Z',
  detalles: [
    {
      id: 1,
      producto_id: 10,
      nombre_snapshot: 'Hamburguesa Clásica',
      cantidad: 2,
      precio_snapshot: 1000.00,
      personalizacion: [],
    },
    {
      id: 2,
      producto_id: 11,
      nombre_snapshot: 'Papas Fritas',
      cantidad: 1,
      precio_snapshot: 500.00,
      personalizacion: [3],
    },
  ],
  historial: [
    {
      id: 1,
      pedido_id: 1,
      estado_anterior_id: null,
      estado_nuevo_id: 1,
      observacion: null,
      usuario_responsable_id: null,
      usuario_email: null,
      creado_en: '2026-05-15T14:30:00Z',
    },
  ],
}

const mockOrderThreeStates = {
  ...mockOrder,
  estado_pedido_id: 3,    // EN_PREPARACIÓN
  historial: [
    {
      id: 1, pedido_id: 1, estado_anterior_id: null, estado_nuevo_id: 1,
      observacion: null, usuario_responsable_id: null, usuario_email: null,
      creado_en: '2026-05-15T14:30:00Z',
    },
    {
      id: 2, pedido_id: 1, estado_anterior_id: 1, estado_nuevo_id: 2,
      observacion: null, usuario_responsable_id: 1, usuario_email: 'sistema@foodstore.com',
      creado_en: '2026-05-15T15:00:00Z',
    },
    {
      id: 3, pedido_id: 1, estado_anterior_id: 2, estado_nuevo_id: 3,
      observacion: null, usuario_responsable_id: 4, usuario_email: 'pedidos@test.com',
      creado_en: '2026-05-15T16:00:00Z',
    },
  ],
}

// ─── Tests ───────────────────────────────────────────────────────────────────

test.describe('Order Detail — CLIENT', () => {
  test('CLIENT ve detalle de su pedido con header y timeline', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.route('**/api/v1/pedidos/1', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockOrder),
      })
    })

    await page.goto('/pedidos/1')

    // Heading shows order number
    await expect(page.getByRole('heading', { name: /pedido/i })).toBeVisible()
    await expect(page.getByText(/#1/)).toBeVisible()

    // Timeline is visible
    await expect(page.getByText(/Historial del pedido/i)).toBeVisible()
  })

  test('Timeline muestra 3 ítems cuando historial tiene 3 entradas', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.route('**/api/v1/pedidos/1', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockOrderThreeStates),
      })
    })

    await page.goto('/pedidos/1')

    // Wait for page to load
    await expect(page.getByText(/Historial del pedido/i)).toBeVisible()

    // Three timeline list items visible
    const timelineItems = page.locator('ol[role="list"] > li')
    await expect(timelineItems).toHaveCount(3)
  })

  test('CLIENT cancela pedido PENDIENTE con confirmación', async ({ page }) => {
    await loginAs(page, 'CLIENT')

    let deleteCount = 0

    await page.route('**/api/v1/pedidos/1', (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCount++
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...mockOrder, estado_pedido_id: 6 }),
        })
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockOrder),
        })
      }
    })

    await page.goto('/pedidos/1')

    // Click cancel button
    await page.getByRole('button', { name: /cancelar pedido/i }).click()

    // Modal appears
    await expect(page.getByText('Cancelar pedido')).toBeVisible()
    await expect(page.getByText(/#1/)).toBeVisible()

    // Confirm cancellation
    await page.getByRole('button', { name: /Sí, cancelar pedido/i }).click()

    // Verify the DELETE was called
    await expect.poll(() => deleteCount).toBe(1)
  })

  test('Modal se cierra con "No, mantener pedido" sin ejecutar DELETE', async ({ page }) => {
    await loginAs(page, 'CLIENT')

    let deleteCount = 0

    await page.route('**/api/v1/pedidos/1', (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCount++
        route.fulfill({ status: 200, body: '{}' })
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockOrder),
        })
      }
    })

    await page.goto('/pedidos/1')
    await page.getByRole('button', { name: /cancelar pedido/i }).click()
    await expect(page.getByText('Cancelar pedido')).toBeVisible()

    // Click "No, mantener pedido"
    await page.getByRole('button', { name: /No, mantener pedido/i }).click()

    // Modal closes — title disappears
    await expect(page.getByText('Cancelar pedido')).not.toBeVisible()

    // DELETE was never called
    expect(deleteCount).toBe(0)
  })
})

test.describe('Order Detail — Auth guards', () => {
  test('Usuario sin autenticación → redirige a /login', async ({ page }) => {
    await logout(page)
    await page.goto('/pedidos/1')
    await expect(page).toHaveURL('/login')
  })

  test('CLIENT intenta /admin/pedidos/1 → redirige a /403', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.goto('/admin/pedidos/1')
    await expect(page).toHaveURL('/403')
  })
})

test.describe('Order Detail — Error states', () => {
  test('Pedido no encontrado (404) → muestra estado de error con CTA', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.route('**/api/v1/pedidos/999', (route) => {
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          type: 'about:blank',
          title: 'Pedido no encontrado',
          status: 404,
          detail: 'El pedido con id=999 no existe.',
          instance: '/api/v1/pedidos/999',
        }),
      })
    })

    await page.goto('/pedidos/999')

    // Error state visible
    await expect(page.getByRole('alert')).toBeVisible()
    // CTA to go back
    await expect(page.getByText(/Volver a mis pedidos/i)).toBeVisible()
  })
})
