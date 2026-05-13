# Tasks: frontend-user-profile-ui

> Git hash at propose time: `630f01c`
> Change type: `frontend catálogo` (closest match) + `custom hooks + optimistic updates`
> Skills aplicadas: tailwind-design-system, ui-design-system, vercel-react-best-practices, frontend-state-management, zustand-state-management, testing-e2e-playwright

---

## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens @theme, sin colores crudos, CVA, Tailwind v4 CSS-first
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — Radix primitives, WCAG AA, ARIA, keyboard nav
- [ ] 0.3 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — React.lazy + Suspense, placeholderData, bundle splitting
- [ ] 0.4 Leer `.agents/skills/frontend-state-management/SKILL.md` — Zustand vs TanStack Query, evitar duplicación
- [ ] 0.5 Leer `.agents/skills/zustand-state-management/README.md` — devtools(persist()), selectores granulares
- [ ] 0.6 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — guards, auth helpers, specs de flujos

---

## 1. Types — Contratos TypeScript del feature

- [ ] 1.1 Crear `frontend/src/features/profile/types/profile.ts` con las interfaces:
  - `PerfilData`: `{ id: number; email: string; nombre: string; telefono: string | null; roles: string[]; creado_en: string }`
  - `UpdatePerfilPayload`: `{ nombre?: string; telefono?: string }` — ambos opcionales, al menos uno requerido
  - `ChangePasswordPayload`: `{ password_actual: string; nueva_password: string }`
  - **[skill: tailwind-design-system]** — no hay lógica de estilo aquí, pero los tipos guían los componentes

---

## 2. Hooks — TanStack Query (estado servidor)

> Regla: TanStack Query para todo estado del servidor. Zustand solo para estado cliente. NO duplicar datos del servidor en Zustand.

- [ ] 2.1 Crear `frontend/src/features/profile/hooks/usePerfil.ts` [skill: frontend-state-management, vercel-react-best-practices]
  - `useQuery({ queryKey: ['perfil'], queryFn: GET /api/v1/perfil })`
  - `staleTime: 60_000` — evitar refetch en cada focus
  - `placeholderData: keepPreviousData` — sin flicker en refocus
  - Usar `apiClient` de `@/shared/api/axios`
  - Tipar con `PerfilData`

- [ ] 2.2 Crear `frontend/src/features/profile/hooks/useUpdatePerfil.ts` [skill: frontend-state-management]
  - `useMutation({ mutationFn: PUT /api/v1/perfil })`
  - `onSuccess`: invalidar `['perfil']` query + `useUIStore.getState().addToast({ message: 'Perfil actualizado.', type: 'success' })`
  - NO manejar `onError` — el interceptor Axios ya despacha toast RFC 7807

- [ ] 2.3 Crear `frontend/src/features/profile/hooks/useCambiarPassword.ts` [skill: frontend-state-management, zustand-state-management]
  - `useMutation({ mutationFn: POST /api/v1/perfil/cambiar-password })`
  - `onSuccess`: toast "Contraseña actualizada. Iniciá sesión nuevamente." + `setTimeout(2000, authStore.logout())`
  - Después del logout, `ProtectedRoute` redirige automáticamente a `/login`
  - NO manejar `onError` — el interceptor Axios ya despacha toast RFC 7807 para 400 y 422

---

## 3. Componentes — feature/profile/components/

### 3.1 `ProfileInfo.tsx` — sección informativa read-only [skill: tailwind-design-system, ui-design-system]

- [ ] 3.1.1 Crear `frontend/src/features/profile/components/ProfileInfo.tsx`
  - Props: `{ perfil: PerfilData | undefined; isLoading: boolean }`
  - Envolver en `<section aria-labelledby="profile-info-heading">` con `<Card>`
  - Mientras `isLoading`: renderizar `<Skeleton>` placeholders con `aria-busy="true"` en el contenedor (no layout shift)
  - Cuando datos disponibles:
    - Email: leer de `authStore` con selector granular `useAuthStore(s => s.user?.email)` — ya disponible, no re-fetchar
    - Nombre: `perfil.nombre`
    - Teléfono: `perfil.telefono ?? 'No especificado'`
    - Roles: `perfil.roles.map(r => <Badge key={r}>{r}</Badge>)` — usar variante `success` para CLIENT, `info` para ADMIN
    - Miembro desde: `new Intl.DateTimeFormat('es-AR', { dateStyle: 'long' }).format(new Date(perfil.creado_en))`

- [ ] 3.1.2 ARIA en `ProfileInfo.tsx` [skill: ui-design-system]
  - `<section>` con `aria-labelledby="profile-info-heading"`
  - `<h2 id="profile-info-heading">Información de cuenta</h2>`
  - Skeleton container: `aria-busy="true"` `aria-label="Cargando perfil"`
  - Badge list: `<ul aria-label="Roles">` con `<li>` por cada badge

- [ ] 3.1.3 Verificar tokens semánticos — **ningún color crudo** [skill: tailwind-design-system]
  - Solo usar: `bg-card`, `text-card-foreground`, `text-foreground`, `text-muted-foreground`, `border-border`, `bg-success`, `text-success-foreground`, `bg-info`, `text-info-foreground`
  - Prohibido: `bg-gray-*`, `text-blue-*`, `text-zinc-*`, o cualquier color Tailwind no semántico

### 3.2 `EditProfileForm.tsx` — formulario editar nombre y teléfono [skill: tailwind-design-system, ui-design-system]

- [ ] 3.2.1 Crear `frontend/src/features/profile/components/EditProfileForm.tsx`
  - Props: `{ perfil: PerfilData | undefined; isLoading: boolean }`
  - Estado local con `useState` para `nombre` y `telefono` (pre-poblados de `perfil` cuando disponible — `useEffect` con `perfil` como dependencia ÚNICA para inicializar)
  - Usar `<Input label="Nombre" id="edit-nombre" ...>` y `<Input label="Teléfono" id="edit-telefono" ...>`
  - Botón submit: `<Button loading={isPending}>Guardar cambios</Button>`

- [ ] 3.2.2 Validación client-side antes de submit [skill: ui-design-system]
  - Al menos un campo modificado (dirty check: `nombre !== perfil.nombre || telefono !== (perfil.telefono ?? '')`)
  - `nombre`: si provisto, longitud 1–100
  - `telefono`: si provisto, longitud máx 20
  - Mostrar errores inline con prop `error` de `<Input>` (activa `aria-invalid` + `role="alert"` automáticamente)
  - NO enviar request si validación falla

- [ ] 3.2.3 ARIA en `EditProfileForm.tsx` [skill: ui-design-system]
  - `<section aria-labelledby="edit-profile-heading">`
  - `<h2 id="edit-profile-heading">Editar perfil</h2>`
  - Errores de validación en `Input` → ya tienen `role="alert"` y `aria-describedby` via el componente existente
  - Botón submit: `aria-busy={isPending}`

- [ ] 3.2.4 Responsive `EditProfileForm.tsx` — mobile-first [skill: tailwind-design-system]
  - Inputs: `w-full` siempre
  - Botón: `w-full sm:w-auto`
  - Card padding: `p-4 sm:p-6`

- [ ] 3.2.5 Verificar tokens semánticos — **ningún color crudo** [skill: tailwind-design-system]
  - Solo usar tokens de `@theme`: `bg-card`, `text-foreground`, `text-muted-foreground`, `border-border`, `ring-ring`, `text-destructive`, `bg-primary`, `text-primary-foreground`

### 3.3 `ChangePasswordForm.tsx` — formulario cambio de contraseña [skill: tailwind-design-system, ui-design-system]

- [ ] 3.3.1 Crear `frontend/src/features/profile/components/ChangePasswordForm.tsx`
  - Estado local: `passwordActual`, `nuevaPassword`, `showPasswordActual`, `showNuevaPassword`
  - Usar `<Input label="Contraseña actual" id="password-actual" type={showPasswordActual ? 'text' : 'password'}>` + botón toggle
  - Usar `<Input label="Nueva contraseña" id="nueva-password" type={showNuevaPassword ? 'text' : 'password'}>` + botón toggle
  - Botón submit: `<Button variant="outline" loading={isPending}>Cambiar contraseña</Button>`

- [ ] 3.3.2 Validación client-side antes de submit [skill: ui-design-system]
  - `passwordActual`: requerida, mín 8 chars
  - `nuevaPassword`: requerida, mín 8 chars
  - `nuevaPassword !== passwordActual` (si iguales → error inline "La nueva contraseña debe ser diferente a la actual")
  - Mostrar errores inline en el `<Input>` correspondiente

- [ ] 3.3.3 Botones toggle show/hide password — ARIA [skill: ui-design-system]
  - `<button type="button" aria-pressed={showPasswordActual} aria-label="Mostrar contraseña actual" onClick={...}>`
  - Icono `Eye` / `EyeOff` de `lucide-react` con `aria-hidden="true"`
  - Posicionado dentro del wrapper del input: `relative` + `absolute right-3 top-1/2 -translate-y-1/2`

- [ ] 3.3.4 ARIA en `ChangePasswordForm.tsx` [skill: ui-design-system]
  - `<section aria-labelledby="change-password-heading">`
  - `<h2 id="change-password-heading">Cambiar contraseña</h2>`
  - Live region para estado post-submit: `<div role="status" aria-live="polite">` (mensaje vacío salvo en éxito)

- [ ] 3.3.5 Responsive `ChangePasswordForm.tsx` — mobile-first [skill: tailwind-design-system]
  - Mismas reglas que `EditProfileForm`: `w-full` inputs, `w-full sm:w-auto` botón

- [ ] 3.3.6 Verificar tokens semánticos — **ningún color crudo** [skill: tailwind-design-system]
  - Solo tokens `@theme` — igual que 3.2.5

---

## 4. Página — `Profile.tsx` (reemplazar stub)

- [ ] 4.1 Reemplazar `frontend/src/pages/Profile.tsx` con la implementación real [skill: vercel-react-best-practices, tailwind-design-system]
  - Importar con paths `@/features/profile/...`
  - Llamar `usePerfil()` en la página — pasar `{ perfil: data, isLoading }` como props a los componentes
  - Layout responsive:

    ```tsx
    <main className="p-4 sm:p-6 lg:p-8" aria-label="Mi Perfil">
      <h1 className="text-2xl font-bold text-foreground mb-6">Mi Perfil</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ProfileInfo perfil={data} isLoading={isLoading} />
        <div className="flex flex-col gap-6">
          <EditProfileForm perfil={data} isLoading={isLoading} />
          <ChangePasswordForm />
        </div>
      </div>
    </main>
    ```

  - Verificar que `React.lazy` ya está en `Router.tsx` — **NO modificar Router.tsx** (ya tiene lazy import)

- [ ] 4.2 Verificar tokens semánticos en `Profile.tsx` — **ningún color crudo** [skill: tailwind-design-system]
  - Usar `text-foreground` para heading, `bg-background` si necesita fondo explícito

- [ ] 4.3 Responsive `Profile.tsx` — verificar en mobile y desktop [skill: tailwind-design-system]
  - Mobile: una columna, padding `p-4`
  - Desktop (lg): dos columnas, padding `p-8`

---

## 5. Tests unitarios — vitest

- [ ] 5.1 Crear `frontend/src/features/profile/__tests__/usePerfil.test.ts` [skill: vercel-react-best-practices]
  - Mock `apiClient.get` con `vi.mock`
  - Test: devuelve datos correctos cuando la API responde 200
  - Test: `isLoading` es `true` durante la petición
  - Test: `isError` es `true` cuando la API falla
  - Wrapper: `QueryClientProvider` con `QueryClient` fresh por test

- [ ] 5.2 Crear `frontend/src/features/profile/__tests__/EditProfileForm.test.tsx` [skill: ui-design-system]
  - Test: renderiza campos pre-poblados con datos del perfil
  - Test: botón deshabilitado si ningún campo fue modificado (dirty check)
  - Test: muestra error inline si `nombre` está vacío al submit
  - Test: muestra error inline si `telefono` tiene más de 20 chars
  - Test: llama a `mutate` con payload correcto cuando validación pasa
  - Mock `useUpdatePerfil` con `vi.mock`

- [ ] 5.3 Crear `frontend/src/features/profile/__tests__/ChangePasswordForm.test.tsx` [skill: ui-design-system]
  - Test: renderiza dos inputs de tipo password por defecto
  - Test: toggle muestra/oculta contraseña (cambia type a 'text')
  - Test: muestra error si nueva contraseña es igual a actual
  - Test: muestra error si passwords menores a 8 chars
  - Test: NO llama a `mutate` si validación falla
  - Test: llama a `mutate` con payload correcto cuando validación pasa
  - Mock `useCambiarPassword` con `vi.mock`

- [ ] 5.4 Verificar coverage ≥ 40% en archivos nuevos del feature [skill: vercel-react-best-practices]
  - Correr: `cd frontend && npx vitest run --coverage`
  - Si < 40% en `features/profile/` → agregar casos adicionales

---

## 6. E2E — Playwright

> Instalar Playwright si no está: `cd frontend && npm install -D @playwright/test && npx playwright install chromium`
> Helper de auth ya definido en skill: `loginAs(page, role)` y `logout(page)` en `e2e/helpers/auth.ts`

- [ ] 6.1 Verificar o crear `frontend/e2e/helpers/auth.ts` con `loginAs` y `logout` [skill: testing-e2e-playwright]
  - Clave de localStorage: `food-store-auth`
  - Usar `page.addInitScript` (NO `page.evaluate` después de navegar — Zustand ya habrá leído estado vacío)
  - Estructura de estado según authStore: `{ state: { isAuthenticated, accessToken, user: { id, email, roles }, _hasHydrated: true }, version: 0 }`

- [ ] 6.2 Crear `frontend/e2e/profile/profile.spec.ts` [skill: testing-e2e-playwright]

  **Escenario 1 — Guard: sin sesión redirige a /login**
  ```ts
  test('redirige a /login sin sesión', async ({ page }) => {
    await logout(page)
    await page.goto('/profile')
    await expect(page).toHaveURL('/login')
  })
  ```

  **Escenario 2 — Carga de datos: perfil renderiza correctamente**
  ```ts
  test('renderiza datos del perfil', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.route('**/api/v1/perfil', route =>
      route.fulfill({ status: 200, body: JSON.stringify({
        id: 2, email: 'cliente@test.com', nombre: 'Juan Test',
        telefono: '1234567890', roles: ['CLIENT'],
        creado_en: '2025-01-01T00:00:00Z'
      }) })
    )
    await page.goto('/profile')
    await expect(page.getByText('Juan Test')).toBeVisible()
    await expect(page.getByText('1234567890')).toBeVisible()
    await expect(page.getByText('CLIENT')).toBeVisible()
  })
  ```

  **Escenario 3 — Edit profile: submit exitoso**
  ```ts
  test('actualiza perfil con nombre nuevo', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.route('**/api/v1/perfil', async route => {
      if (route.request().method() === 'GET')
        return route.fulfill({ status: 200, body: JSON.stringify({ id: 2, email: 'cliente@test.com', nombre: 'Juan', telefono: null, roles: ['CLIENT'], creado_en: '2025-01-01T00:00:00Z' }) })
      return route.fulfill({ status: 200, body: JSON.stringify({ id: 2, email: 'cliente@test.com', nombre: 'Juan Actualizado', telefono: null, roles: ['CLIENT'], creado_en: '2025-01-01T00:00:00Z' }) })
    })
    await page.goto('/profile')
    await page.fill('#edit-nombre', 'Juan Actualizado')
    await page.click('button:has-text("Guardar cambios")')
    await expect(page.locator('text=Perfil actualizado.')).toBeVisible({ timeout: 5000 })
  })
  ```

  **Escenario 4 — Change password: submit exitoso → logout**
  ```ts
  test('cambia contraseña y redirige a login', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.route('**/api/v1/perfil', route =>
      route.fulfill({ status: 200, body: JSON.stringify({ id: 2, email: 'cliente@test.com', nombre: 'Juan', telefono: null, roles: ['CLIENT'], creado_en: '2025-01-01T00:00:00Z' }) })
    )
    await page.route('**/api/v1/perfil/cambiar-password', route =>
      route.fulfill({ status: 204, body: '' })
    )
    await page.goto('/profile')
    await page.fill('#password-actual', 'contraseña1')
    await page.fill('#nueva-password', 'contraseña2')
    await page.click('button:has-text("Cambiar contraseña")')
    await expect(page.locator('text=Contraseña actualizada')).toBeVisible({ timeout: 5000 })
    await expect(page).toHaveURL('/login', { timeout: 5000 })
  })
  ```

  **Escenario 5 — Validación client-side: nueva contraseña = actual**
  ```ts
  test('muestra error si nueva contraseña es igual a la actual', async ({ page }) => {
    await loginAs(page, 'CLIENT')
    await page.route('**/api/v1/perfil', route =>
      route.fulfill({ status: 200, body: JSON.stringify({ id: 2, email: 'cliente@test.com', nombre: 'Juan', telefono: null, roles: ['CLIENT'], creado_en: '2025-01-01T00:00:00Z' }) })
    )
    await page.goto('/profile')
    await page.fill('#password-actual', 'mismaclave')
    await page.fill('#nueva-password', 'mismaclave')
    await page.click('button:has-text("Cambiar contraseña")')
    // Validación client-side — no debe haber llamada al backend
    await expect(page.locator('text=La nueva contraseña debe ser diferente')).toBeVisible()
    // Verificar que no se hizo request al backend
    // (Playwright interceptaría la route si se llamara)
  })
  ```

- [ ] 6.3 Configurar `frontend/playwright.config.ts` si no existe [skill: testing-e2e-playwright]
  - `testDir: './e2e'`, `baseURL: 'http://localhost:5173'`
  - `webServer.command: 'npm run dev'`, `reuseExistingServer: true`

- [ ] 6.4 Agregar scripts en `frontend/package.json` si no existen [skill: testing-e2e-playwright]
  - `"e2e": "playwright test"`
  - `"e2e:ui": "playwright test --ui"`

---

## 7. Verificación final

- [ ] 7.1 Correr tests unitarios `cd frontend && npx vitest run` — todos pasan [skill: vercel-react-best-practices]
- [ ] 7.2 Correr lint `cd frontend && npm run lint` — sin errores [skill: tailwind-design-system]
- [ ] 7.3 Correr build TypeScript `cd frontend && npx tsc --noEmit` — sin errores de tipos [skill: vercel-react-best-practices]
- [ ] 7.4 Auditoría visual — ningún color crudo [skill: tailwind-design-system]
  - Buscar en archivos nuevos: `bg-gray`, `bg-blue`, `text-gray`, `text-blue`, `text-zinc`, `border-gray` → debe dar cero resultados
  - Buscar en archivos nuevos: `text-white`, `text-black`, `bg-white`, `bg-black` → debe dar cero resultados
- [ ] 7.5 Verificación ARIA — keyboard nav manual [skill: ui-design-system]
  - Tab en `/profile` navega por: campos de perfil info → input nombre → input teléfono → botón guardar → input password actual → toggle show → input nueva password → toggle show → botón cambiar
  - Enter en botón submit activa submit
  - Inputs inválidos muestran mensaje de error vinculado (aria-describedby)
- [ ] 7.6 Verificación responsive — visual [skill: tailwind-design-system]
  - En viewport 375px: una columna, todos los elementos accesibles sin scroll horizontal
  - En viewport 1280px: dos columnas, forms en columna derecha
- [ ] 7.7 Correr E2E `cd frontend && npx playwright test e2e/profile/` — todos los escenarios pasan [skill: testing-e2e-playwright]

---

## 8. Checklist Pre-Commit (del AGENTS.md)

- [ ] ¿Imports frontend usando `@/` (path alias)? ✅ sí
- [ ] ¿Estado servidor en TanStack Query, estado cliente en Zustand? ✅ sí
- [ ] ¿NUNCA `useEffect` + fetch donde TanStack Query aplica? ✅ sí (solo useEffect para pre-poblar formulario)
- [ ] ¿`React.lazy` + `Suspense` — Profile ya está configurado en Router.tsx? ✅ ya estaba
- [ ] ¿Tokens semánticos del `@theme` en todos los estilos? ✅ verificado en 7.4
- [ ] ¿ARIA mínimo viable en todos los componentes nuevos? ✅ verificado en 7.5
- [ ] ¿Responsive mobile-first? ✅ verificado en 7.6
- [ ] ¿Tests escritos con vitest (no jest)? ✅ sí
- [ ] ¿Coverage frontend ≥ 40%? ✅ verificado en 5.4
- [ ] ¿Conventional Commits sin co-authored-by? ✅ aplicar en el commit
