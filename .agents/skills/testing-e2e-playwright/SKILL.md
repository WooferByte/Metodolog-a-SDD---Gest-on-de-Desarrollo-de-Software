---
name: testing-e2e-playwright
description: >
  E2E testing con Playwright para Food Store: autenticación JWT vía Zustand v5,
  guards de rutas por rol, toasts del interceptor Axios, formularios login/registro,
  y errores HTTP del backend FastAPI.
  Trigger: cuando se implementan rutas protegidas, flujos de auth, formularios de
  login/registro, toasts de error, o cualquier flujo que requiera verificación
  end-to-end en este proyecto.
license: Apache-2.0
metadata:
  author: food-store-team
  version: "1.0"
---

## When to Use

- Change incluye rutas protegidas con `ProtectedRoute` (redirect a `/login` o `/403`)
- Change incluye formularios de login o registro
- Change incluye toasts disparados por el interceptor Axios
- Change incluye flujos que dependen del rol del usuario (ADMIN, CLIENT, STOCK, PEDIDOS)
- Change requiere verificar comportamiento con backend FastAPI corriendo

## Setup del Proyecto

```bash
# Instalar Playwright (desde frontend/)
cd frontend
npm install -D @playwright/test
npx playwright install chromium

# Crear playwright.config.ts en frontend/
```

```ts
// frontend/playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  baseURL: 'http://localhost:5173',
  use: {
    headless: true,
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
  },
})
```

```bash
# Scripts en package.json
"e2e": "playwright test",
"e2e:ui": "playwright test --ui",
"e2e:debug": "playwright test --debug"
```

## Critical Patterns

### 1. Seedear auth state en localStorage (NO usar UI para login)

La clave de localStorage es `food-store-auth`. El estado tiene esta estructura exacta:

```ts
// frontend/e2e/helpers/auth.ts
import { Page } from '@playwright/test'

type Role = 'ADMIN' | 'CLIENT' | 'STOCK' | 'PEDIDOS'

const USERS: Record<Role, { id: number; email: string }> = {
  ADMIN:   { id: 1, email: 'admin@foodstore.com' },
  CLIENT:  { id: 2, email: 'cliente@test.com' },
  STOCK:   { id: 3, email: 'stock@test.com' },
  PEDIDOS: { id: 4, email: 'pedidos@test.com' },
}

export async function loginAs(page: Page, role: Role, token = 'test-token') {
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

export async function logout(page: Page) {
  await page.addInitScript(() => {
    localStorage.removeItem('food-store-auth')
  })
}
```

> **CRÍTICO**: Usar `addInitScript` (se ejecuta ANTES de que React hidrate).
> Nunca usar `page.evaluate` para setear localStorage después de navegar — Zustand ya habrá leído el estado vacío.

### 2. Esperar hidratación de Zustand antes de assertions

```ts
// Zustand necesita rehydratar antes de que ProtectedRoute decida redirigir
await page.waitForFunction(() => {
  const raw = localStorage.getItem('food-store-auth')
  if (!raw) return true // sin sesión también OK
  const parsed = JSON.parse(raw)
  return parsed?.state?._hasHydrated === true
})
```

### 3. Verificar toasts del interceptor Axios

El `ToastContainer` está en `fixed bottom-4 right-4`. Los toasts tienen `role="alert"` implícito por ser dinámicos:

```ts
// Esperar que aparezca un toast con mensaje específico
await expect(page.locator('[data-testid="toast"]').first()).toBeVisible()
await expect(page.locator('text=El recurso solicitado no existe')).toBeVisible()

// O por tipo de toast
await expect(page.locator('.toast-error').first()).toBeVisible({ timeout: 5000 })
```

> Agregar `data-testid="toast"` al div raíz de cada toast en `ToastContainer.tsx` para selectores estables.

### 4. Mockear backend FastAPI con `page.route`

```ts
// Mock 404 para disparar toast del interceptor
await page.route('**/api/v1/**', route => {
  route.fulfill({
    status: 404,
    contentType: 'application/json',
    body: JSON.stringify({
      type: 'about:blank',
      title: 'Not Found',
      status: 404,
      detail: 'Recurso no encontrado',
      instance: '/api/v1/test',
    }),
  })
})

// Mock 500
await page.route('**/api/v1/**', route => {
  route.fulfill({ status: 500, body: JSON.stringify({ status: 500, detail: 'Error interno' }) })
})

// Mock éxito login
await page.route('**/api/v1/auth/login', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify({
      access_token: 'fake-jwt-token',
      refresh_token: 'fake-refresh',
      token_type: 'bearer',
      usuario: { id: 1, email: 'admin@foodstore.com', nombre: 'Admin', activo: true },
    }),
  })
})
```

### 5. Route guards — patrones de redirect

```ts
// Guard → /login (sin autenticación)
await logout(page)
await page.goto('/profile')
await expect(page).toHaveURL('/login')

// Guard → /403 (rol insuficiente)
await loginAs(page, 'CLIENT')
await page.goto('/admin/usuarios')
await expect(page).toHaveURL('/403')
await expect(page.getByRole('heading', { name: 'Acceso denegado' })).toBeVisible()

// Guard → acceso permitido
await loginAs(page, 'ADMIN')
await page.goto('/admin/usuarios')
await expect(page).not.toHaveURL('/login')
await expect(page).not.toHaveURL('/403')
```

## Code Examples

### Test: flujo completo de login

```ts
// frontend/e2e/auth/login.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Login', () => {
  test('redirige a /login en ruta protegida sin sesión', async ({ page }) => {
    await page.goto('/profile')
    await expect(page).toHaveURL('/login')
  })

  test('muestra error con credenciales incorrectas', async ({ page }) => {
    await page.route('**/api/v1/auth/login', route =>
      route.fulfill({ status: 401, body: JSON.stringify({ detail: 'Invalid credentials' }) })
    )
    await page.goto('/login')
    await page.fill('input[type="email"]', 'wrong@test.com')
    await page.fill('input[type="password"]', 'wrongpass')
    await page.click('button[type="submit"]')
    await expect(page.locator('text=Credenciales inválidas')).toBeVisible()
  })

  test('login exitoso redirige al home', async ({ page }) => {
    await page.route('**/api/v1/auth/login', route =>
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          access_token: 'valid-token',
          refresh_token: 'valid-refresh',
          token_type: 'bearer',
          usuario: { id: 1, email: 'admin@foodstore.com', nombre: 'Admin', activo: true },
        }),
      })
    )
    await page.goto('/login')
    await page.fill('input[type="email"]', 'admin@foodstore.com')
    await page.fill('input[type="password"]', 'admin123456')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL('/')
  })
})
```

### Test: guards de ruta por rol

```ts
// frontend/e2e/auth/route-guards.spec.ts
import { test, expect } from '@playwright/test'
import { loginAs, logout } from '../helpers/auth'

test.describe('Route Guards', () => {
  test('CLIENT no puede acceder a /admin/usuarios → 403', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.goto('/admin/usuarios')
    await expect(page).toHaveURL('/403')
    await expect(page.getByRole('heading', { name: 'Acceso denegado' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Volver al inicio' })).toBeVisible()
  })

  test('ADMIN puede acceder a /admin/usuarios', async ({ page }) => {
    await loginAs(page, 'ADMIN')
    await page.goto('/admin/usuarios')
    await expect(page).not.toHaveURL('/403')
    await expect(page).not.toHaveURL('/login')
  })

  test('sin sesión → /profile redirige a /login', async ({ page }) => {
    await logout(page)
    await page.goto('/profile')
    await expect(page).toHaveURL('/login')
  })
})
```

### Test: toasts del interceptor HTTP

```ts
// frontend/e2e/errors/http-toasts.spec.ts
import { test, expect } from '@playwright/test'
import { loginAs } from '../helpers/auth'

test.describe('HTTP Error Toasts', () => {
  test('404 muestra toast info', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.route('**/api/v1/productos', route =>
      route.fulfill({ status: 404, body: JSON.stringify({ status: 404, detail: 'Not found' }) })
    )
    await page.goto('/')
    // Trigger request via app action or directly
    await expect(page.locator('text=El recurso solicitado no existe').or(
      page.locator('text=Not found')
    )).toBeVisible({ timeout: 5000 })
  })

  test('500 muestra toast error', async ({ page }) => {
    await loginAs(page, 'ADMIN')
    await page.route('**/api/v1/**', route =>
      route.fulfill({ status: 500, body: JSON.stringify({ status: 500 }) })
    )
    await page.goto('/')
    await expect(page.locator('text=Error del servidor')).toBeVisible({ timeout: 5000 })
  })
})
```

## Commands

```bash
# Correr todos los e2e (requiere npm run dev corriendo)
cd frontend && npx playwright test

# Correr un archivo específico
npx playwright test e2e/auth/route-guards.spec.ts

# Modo UI (recomendado para desarrollo)
npx playwright test --ui

# Debug interactivo
npx playwright test --debug

# Ver reporte HTML
npx playwright show-report

# Con backend real (FastAPI debe estar en :8000)
PLAYWRIGHT_BASE_URL=http://localhost:5173 npx playwright test
```

## Estructura de Archivos

```
frontend/
├── e2e/
│   ├── helpers/
│   │   └── auth.ts          ← loginAs(), logout()
│   ├── auth/
│   │   ├── login.spec.ts
│   │   ├── register.spec.ts
│   │   └── route-guards.spec.ts
│   ├── errors/
│   │   └── http-toasts.spec.ts
│   └── catalog/
│       └── catalog.spec.ts
├── playwright.config.ts
└── package.json
```

## Resources

- **Helper de auth**: Ver [assets/auth-helper.ts](assets/auth-helper.ts)
- **Config Playwright**: Ver [assets/playwright.config.ts](assets/playwright.config.ts)
