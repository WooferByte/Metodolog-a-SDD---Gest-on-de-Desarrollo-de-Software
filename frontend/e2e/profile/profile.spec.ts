/**
 * E2E tests for /profile page.
 *
 * Scenarios:
 *   1. Guard: unauthenticated → redirects to /login
 *   2. Load: authenticated CLIENT → page renders profile data
 *   3. Edit profile: submit with new nombre → success toast visible
 *   4. Change password: submit valid → toast + redirect to /login
 *   5. Validation: nueva password = actual → client-side error, no API call
 *
 * Strategy:
 *   - loginAs/logout helpers seed localStorage BEFORE React hydrates (addInitScript)
 *   - Backend mocked with page.route (no real backend needed)
 */

import { test, expect } from '@playwright/test'
import { loginAs, logout } from '../helpers/auth'

const mockPerfil = {
  id: 2,
  email: 'cliente@test.com',
  nombre: 'Juan Test',
  telefono: '1234567890',
  roles: ['CLIENT'],
  creado_en: '2025-01-01T00:00:00Z',
}

// ── Scenario 1: Guard ─────────────────────────────────────────────────────────

test('redirige a /login sin sesión activa', async ({ page }) => {
  await logout(page)
  await page.goto('/profile')
  await expect(page).toHaveURL('/login')
})

// ── Scenario 2: Load ──────────────────────────────────────────────────────────

test('renderiza datos del perfil con sesión CLIENT', async ({ page }) => {
  await loginAs(page, 'CLIENT')

  await page.route('**/api/v1/perfil', (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPerfil),
      })
    }
    return route.continue()
  })

  await page.goto('/profile')

  await expect(page.getByText('Juan Test')).toBeVisible({ timeout: 5000 })
  await expect(page.getByText('1234567890')).toBeVisible()
  await expect(page.getByText('CLIENT')).toBeVisible()
})

// ── Scenario 3: Edit profile ──────────────────────────────────────────────────

test('actualiza perfil con nombre nuevo y muestra toast de éxito', async ({ page }) => {
  await loginAs(page, 'CLIENT')

  await page.route('**/api/v1/perfil', async (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPerfil),
      })
    }
    if (route.request().method() === 'PUT') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...mockPerfil, nombre: 'Juan Actualizado' }),
      })
    }
    return route.continue()
  })

  await page.goto('/profile')
  // Wait for data to load
  await expect(page.getByText('Juan Test')).toBeVisible({ timeout: 5000 })

  // Edit nombre
  await page.fill('#edit-nombre', 'Juan Actualizado')
  await page.click('button:has-text("Guardar cambios")')

  // Success toast dispatched by useUpdatePerfil onSuccess
  await expect(page.getByText('Perfil actualizado.')).toBeVisible({ timeout: 5000 })
})

// ── Scenario 4: Change password ───────────────────────────────────────────────

test('cambia contraseña, muestra toast y redirige a /login', async ({ page }) => {
  await loginAs(page, 'CLIENT')

  await page.route('**/api/v1/perfil', (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPerfil),
      })
    }
    return route.continue()
  })

  await page.route('**/api/v1/perfil/cambiar-password', (route) => {
    return route.fulfill({
      status: 204,
      body: '',
    })
  })

  await page.goto('/profile')
  await expect(page.getByText('Juan Test')).toBeVisible({ timeout: 5000 })

  await page.fill('#password-actual', 'contraseña1')
  await page.fill('#nueva-password', 'contraseña2')
  await page.click('button:has-text("Cambiar contraseña")')

  // Toast from useCambiarPassword onSuccess
  await expect(page.getByText(/Contraseña actualizada/)).toBeVisible({ timeout: 5000 })

  // After 2000ms logout → ProtectedRoute redirects to /login
  await expect(page).toHaveURL('/login', { timeout: 5000 })
})

// ── Scenario 5: Client-side validation ───────────────────────────────────────

test('muestra error si nueva contraseña es igual a la actual', async ({ page }) => {
  await loginAs(page, 'CLIENT')

  await page.route('**/api/v1/perfil', (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPerfil),
      })
    }
    return route.continue()
  })

  await page.goto('/profile')
  await expect(page.getByText('Juan Test')).toBeVisible({ timeout: 5000 })

  await page.fill('#password-actual', 'mismaclave1')
  await page.fill('#nueva-password', 'mismaclave1')
  await page.click('button:has-text("Cambiar contraseña")')

  // Client-side validation — no request should hit the backend
  await expect(
    page.getByText('La nueva contraseña debe ser diferente a la actual.'),
  ).toBeVisible()
})
