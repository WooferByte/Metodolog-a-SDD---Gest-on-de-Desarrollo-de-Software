/**
 * E2E Tests: Route Guards
 *
 * Tests ProtectedRoute guard behavior for:
 * 1. Unauthenticated access → redirect to /login
 * 2. Authenticated CLIENT → access denied to ADMIN-only routes → /403
 * 3. Authenticated ADMIN → full access to admin routes
 *
 * Auth strategy: seed localStorage with loginAs() BEFORE React hydrates,
 * so Zustand reads the correct state on first render (no flash redirect).
 */

import { test, expect } from '@playwright/test'
import { loginAs, logout } from './helpers/auth'

test.describe('Route Guards', () => {
  // ── Test 1 ─────────────────────────────────────────────────────────────────
  test('unauthenticated → /profile → redirects to /login', async ({ page }) => {
    await logout(page)
    await page.goto('/profile')
    await expect(page).toHaveURL('/login')
  })

  // ── Test 2 ─────────────────────────────────────────────────────────────────
  test('unauthenticated → /admin → redirects to /login', async ({ page }) => {
    await logout(page)
    await page.goto('/admin')
    await expect(page).toHaveURL('/login')
  })

  // ── Test 3 ─────────────────────────────────────────────────────────────────
  test('CLIENT → /admin/usuarios (ADMIN-only) → redirects to /403', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.goto('/admin/usuarios')
    await expect(page).toHaveURL('/403')
  })

  // ── Test 4 ─────────────────────────────────────────────────────────────────
  test('ADMIN → /admin/usuarios → renders without redirect', async ({ page }) => {
    await loginAs(page, 'ADMIN')
    await page.goto('/admin/usuarios')
    await expect(page).not.toHaveURL('/login')
    await expect(page).not.toHaveURL('/403')
  })
})
