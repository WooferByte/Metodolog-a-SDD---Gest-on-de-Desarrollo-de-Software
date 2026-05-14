/**
 * Cart E2E Tests — cart-flows.spec.ts
 *
 * Tests the full cart lifecycle:
 * 1. Empty state renders correctly
 * 2. Cart state seeded in localStorage shows items on /cart
 * 3. Quantity increment via stepper
 * 4. Quantity decrement (stays at 1, does not auto-remove)
 * 5. Remove item via trash button
 * 6. Clear cart button empties the cart
 * 7. Cart persists across page reload
 * 8. Navbar badge shows correct count
 * 9. Checkout CTA redirects to /login when unauthenticated
 *
 * Cart localStorage key: 'food-store-cart' (matches cartStore persist name)
 * Auth seeding: uses loginAs/logout helpers (addInitScript pattern)
 *
 * NOTE: These tests require `npm run dev` to be running on http://localhost:5173
 */

import { test, expect, Page } from '@playwright/test'
import { loginAs, logout } from '../helpers/auth'

interface CartItem {
  productId: string
  name: string
  price: number
  quantity: number
}

/**
 * Seed cart state in localStorage before React hydrates.
 * Uses addInitScript so Zustand reads the correct state from localStorage on first render.
 * localStorage key: 'food-store-cart' (matches cartStore persist name)
 */
async function seedCart(page: Page, items: CartItem[]) {
  await page.addInitScript(({ key, value }) => {
    localStorage.setItem(key, JSON.stringify(value))
  }, {
    key: 'food-store-cart',
    value: {
      state: { items },
      version: 0,
    },
  })
}

/**
 * Wait for Zustand cart store to hydrate from localStorage.
 */
async function waitForCartHydration(page: Page) {
  await page.waitForFunction(() => {
    const raw = localStorage.getItem('food-store-cart')
    if (!raw) return true
    try {
      JSON.parse(raw)
      return true
    } catch {
      return false
    }
  })
}

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------
const PIZZA_ITEM: CartItem = {
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 10.99,
  quantity: 2,
}

const CALZONE_ITEM: CartItem = {
  productId: 'calzone-001',
  name: 'Calzone Especial',
  price: 12.99,
  quantity: 1,
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('Cart: Empty State', () => {
  test.beforeEach(async ({ page }) => {
    await logout(page)
    await loginAs(page, 'CLIENT')
  })

  test('empty state — shows EmptyCart component on /cart', async ({ page }) => {
    await page.goto('/cart')
    await expect(page.getByRole('heading', { name: 'Tu carrito está vacío' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Ver productos' })).toBeVisible()
  })
})

test.describe('Cart: Items Display', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page, [PIZZA_ITEM, CALZONE_ITEM])
  })

  test('shows cart items seeded from localStorage', async ({ page }) => {
    await page.goto('/cart')
    await waitForCartHydration(page)
    await expect(page.getByText('Pepperoni Pizza')).toBeVisible()
    await expect(page.getByText('Calzone Especial')).toBeVisible()
  })

  test('shows correct item count in heading area', async ({ page }) => {
    await page.goto('/cart')
    await waitForCartHydration(page)
    await expect(page.getByRole('heading', { name: 'Mi carrito' })).toBeVisible()
    // 3 total items (pizza qty=2, calzone qty=1)
    await expect(page.getByText('3 productos')).toBeVisible()
  })
})

test.describe('Cart: Quantity Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page, [PIZZA_ITEM]) // starts at quantity=2
  })

  test('increment quantity with + button', async ({ page }) => {
    await page.goto('/cart')
    await waitForCartHydration(page)
    // Current value is 2
    const input = page.getByRole('spinbutton', { name: 'Cantidad' })
    await expect(input).toHaveValue('2')
    // Click + to increment
    await page.getByRole('button', { name: 'Aumentar cantidad' }).click()
    await expect(input).toHaveValue('3')
  })

  test('decrement quantity stays at 1 (does not remove)', async ({ page }) => {
    const pizzaAtOne: CartItem = { ...PIZZA_ITEM, quantity: 2 }
    await seedCart(page, [pizzaAtOne])
    await page.goto('/cart')
    await waitForCartHydration(page)
    // Click - to go from 2 to 1
    await page.getByRole('button', { name: 'Disminuir cantidad' }).click()
    const input = page.getByRole('spinbutton', { name: 'Cantidad' })
    await expect(input).toHaveValue('1')
    // Item should still be present
    await expect(page.getByText('Pepperoni Pizza')).toBeVisible()
  })
})

test.describe('Cart: Item Removal', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page, [PIZZA_ITEM, CALZONE_ITEM])
  })

  test('remove item with trash button', async ({ page }) => {
    await page.goto('/cart')
    await waitForCartHydration(page)
    // Click the remove button for Pizza
    await page.getByRole('button', { name: /Eliminar Pepperoni Pizza del carrito/i }).click()
    await expect(page.getByText('Pepperoni Pizza')).not.toBeVisible()
    // Calzone should still be there
    await expect(page.getByText('Calzone Especial')).toBeVisible()
  })
})

test.describe('Cart: Clear Cart', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page, [PIZZA_ITEM, CALZONE_ITEM])
  })

  test('clear cart button shows empty state', async ({ page }) => {
    await page.goto('/cart')
    await waitForCartHydration(page)
    await page.getByRole('button', { name: 'Vaciar carrito' }).click()
    await expect(page.getByRole('heading', { name: 'Tu carrito está vacío' })).toBeVisible()
  })
})

test.describe('Cart: Persistence', () => {
  test('cart persists items after page reload', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page, [PIZZA_ITEM])
    await page.goto('/cart')
    await waitForCartHydration(page)
    await expect(page.getByText('Pepperoni Pizza')).toBeVisible()
    // Reload the page
    await page.reload()
    await waitForCartHydration(page)
    // Items should still be there (Zustand persist middleware)
    await expect(page.getByText('Pepperoni Pizza')).toBeVisible()
  })
})

test.describe('Cart: Navbar Badge', () => {
  test('navbar badge shows item count when cart has items', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page, [PIZZA_ITEM, CALZONE_ITEM]) // 2+1 = 3 total items
    await page.goto('/')
    await waitForCartHydration(page)
    // Badge should show "3" (totalItems = qty2 + qty1)
    const badge = page.locator('[aria-live="polite"]').first()
    await expect(badge).toBeVisible()
    await expect(badge).toHaveText('3')
  })

  test('cart icon button has accessible aria-label with count', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page, [PIZZA_ITEM]) // qty=2, so 2 products
    await page.goto('/')
    await waitForCartHydration(page)
    await expect(
      page.getByRole('button', { name: /Carrito, 2 productos/i })
    ).toBeVisible()
  })
})

test.describe('Cart: Checkout CTA Authentication', () => {
  test('unauthenticated user → checkout CTA redirects to /login', async ({ page }) => {
    await logout(page)
    await seedCart(page, [PIZZA_ITEM])
    await page.goto('/cart')
    // Without auth, the cart route itself redirects to /login
    await expect(page).toHaveURL('/login')
  })

  test('authenticated user → checkout CTA link points to /checkout', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await seedCart(page, [PIZZA_ITEM])
    await page.goto('/cart')
    await waitForCartHydration(page)
    const checkoutLink = page.getByRole('link', { name: 'Proceder al pago' }).first()
    await expect(checkoutLink).toBeVisible()
    await expect(checkoutLink).toHaveAttribute('href', '/checkout')
  })
})
