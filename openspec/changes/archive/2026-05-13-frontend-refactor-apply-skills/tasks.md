## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens @theme, design system Tailwind v4 CSS-first, reemplazar colores crudos con tokens semánticos
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — Radix primitives, WCAG AA, ARIA roles, keyboard nav, accesibilidad mínima viable
- [ ] 0.3 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — code splitting con React.lazy, Suspense, placeholderData, eliminar dead code
- [ ] 0.4 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación estado servidor (TanStack Query) vs cliente (Zustand), evitar duplicación
- [ ] 0.5 Leer `.agents/skills/zustand-state-management/README.md` — devtools middleware, selectores granulares, Zustand v5 patterns
- [ ] 0.6 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — setup Playwright, loginAs helper con localStorage seed, specs de guards por rol

---

## 1. Code Splitting — Router.tsx [vercel-react-best-practices]

> **Contexto**: `frontend/src/app/Router.tsx` tiene todos los pages como imports estáticos — el bundle completo se descarga al arrancar. Convertir a lazy imports.

- [ ] 1.1 Leer `frontend/src/app/Router.tsx` para ver el estado actual de imports y rutas
- [ ] 1.2 Extraer spinner de carga a `frontend/src/shared/components/ui/Spinner.tsx` — reutilizar el markup del spinner existente en `withAuth.tsx` (`h-8 w-8 animate-spin rounded-full border-4 border-border border-t-foreground`)
- [ ] 1.3 En `Router.tsx`, reemplazar todos los imports estáticos de páginas por `React.lazy()`:
  ```tsx
  import { lazy, Suspense } from 'react'
  const Catalog      = lazy(() => import('@/pages/Catalog'))
  const Login        = lazy(() => import('@/pages/Login'))
  const Register     = lazy(() => import('@/pages/Register'))
  const NotFound     = lazy(() => import('@/pages/NotFound'))
  const ForbiddenPage = lazy(() => import('@/pages/ForbiddenPage'))
  const Profile      = lazy(() => import('@/pages/Profile'))
  const Orders       = lazy(() => import('@/pages/Orders'))
  const Admin        = lazy(() => import('@/pages/Admin'))
  ```
- [ ] 1.4 Envolver `<Routes>` en `<Suspense fallback={<Spinner />}>` en Router.tsx
- [ ] 1.5 Verificar que `npm run build` no tire errores y que el bundle analysis muestre chunks separados por página (`npx vite build --debug`)

---

## 2. Zustand devtools — authStore y cartStore [zustand-state-management]

> **Contexto**: `authStore.ts` y `cartStore.ts` usan `persist()` pero no `devtools()`. Sin devtools, el estado no es inspeccionable en Redux DevTools. Orden correcto en Zustand v5: `devtools(persist(...))`.

- [ ] 2.1 Leer `frontend/src/store/authStore.ts` y `frontend/src/store/cartStore.ts` para ver la estructura actual
- [ ] 2.2 En `authStore.ts`: importar `devtools` de `zustand/middleware` y wrappear `persist(...)` con `devtools(..., { name: 'AuthStore' })`
- [ ] 2.3 En `cartStore.ts`: mismo patrón — `devtools(persist(...), { name: 'CartStore' })`
- [ ] 2.4 Verificar que los tipos `AuthStore` y `CartStore` en `types.ts` no requieren ajuste (los tipos son de la store, no del middleware)
- [ ] 2.5 Correr `npx vitest run store/` para confirmar que los tests de authStore y cartStore siguen en verde

---

## 3. Eliminar HOC deprecated — withAuth.tsx [vercel-react-best-practices]

> **Contexto**: `frontend/src/shared/routing/withAuth.tsx` exporta una función `withAuth` marcada como `@deprecated`. Nadie la usa (Router.tsx solo usa `ProtectedRoute`). Es dead code.

- [ ] 3.1 Buscar todos los usos de `withAuth` en el proyecto: `grep -r "withAuth" frontend/src --include="*.tsx" --include="*.ts"`
- [ ] 3.2 Confirmar que solo `ProtectedRoute` se importa de ese archivo y que `withAuth` no tiene consumidores
- [ ] 3.3 Eliminar la función `withAuth` y su JSDoc de `withAuth.tsx` — solo conservar `ProtectedRoute` y `ProtectedRouteProps`
- [ ] 3.4 Actualizar el nombre del archivo si tiene sentido: considerar renombrar a `ProtectedRoute.tsx` y actualizar el import en `Router.tsx`
- [ ] 3.5 Correr `npx tsc --noEmit` para confirmar que no quedan referencias rotas

---

## 4. Tokens semánticos — Componentes de products [tailwind-design-system]

> **Contexto**: El CSS global tiene los tokens `@theme` correctos (OKLCH, bg-primary, text-muted-foreground, etc.) pero algunos componentes usan colores crudos de la paleta Tailwind. Regla: ningún componente en `features/products/` debe usar colores crudos.

- [ ] 4.1 Leer `frontend/src/features/products/components/Pagination.tsx` — tiene `bg-blue-600` confirmado
- [ ] 4.2 Leer `frontend/src/features/products/components/ProductCard.tsx`, `ProductDetail.tsx`, `ProductGrid.tsx`, `FilterBar.tsx`, `CategoryFilter.tsx`, `AllergenFilter.tsx`, `AppliedFilters.tsx`, `SearchInput.tsx`
- [ ] 4.3 En `Pagination.tsx`: reemplazar `bg-blue-600 text-white` (botón de página activa) con `bg-primary text-primary-foreground`
- [ ] 4.4 Auditar todos los componentes de `products/components/` y reemplazar colores crudos:
  | Patrón a buscar | Reemplazar con |
  |----------------|----------------|
  | `bg-blue-*` | `bg-primary` / `bg-accent` |
  | `text-gray-*` | `text-muted-foreground` / `text-foreground` |
  | `border-gray-*` | `border-border` |
  | `bg-green-*` | `bg-success/10` |
  | `text-green-*` | `text-success` |
  | `bg-red-*` | `bg-destructive/10` |
  | `text-red-*` | `text-destructive` |
- [ ] 4.5 Correr `npx tsc --noEmit` y `npx vitest run` para confirmar sin regresiones

---

## 5. ARIA mínimo viable — Componentes de catálogo [ui-design-system]

> **Contexto**: El catálogo tiene funcionalidad completa pero carece de atributos ARIA en varios puntos clave. Aplicar WCAG AA mínimo a los componentes existentes sin rediseñar.

- [ ] 5.1 En `ProductGrid.tsx` (o donde se renderice la lista de productos): agregar `role="list"` al contenedor del grid y `role="listitem"` a cada card wrapper
- [ ] 5.2 En `ProductCard.tsx`:
  - Confirmar que el botón "Agregar al carrito" tiene `aria-label` con el nombre del producto
  - Confirmar que la imagen tiene `alt` descriptivo
  - Agregar `aria-label` al botón de ver detalles si no tiene texto visible
- [ ] 5.3 En `ProductDetail.tsx` (modal):
  - Agregar `role="dialog"`, `aria-modal="true"`, `aria-labelledby` apuntando al ID del título del producto
  - Asegurar que el botón de cerrar tiene `aria-label="Cerrar"`
  - Confirmar que al abrir el modal el foco se mueve al modal
- [ ] 5.4 En `FilterBar.tsx` o el contenedor de resultados: agregar `aria-live="polite"` a la región que muestra el conteo de resultados (ej: "85 productos encontrados")
- [ ] 5.5 En `SearchInput.tsx`: confirmar que el input tiene `aria-label` o `<label>` asociado
- [ ] 5.6 En `Pagination.tsx`: confirmar `aria-label` en el `<nav>`, `aria-current="page"` en el botón de página activa, `aria-disabled` en botones deshabilitados (ya existe — solo verificar)
- [ ] 5.7 Correr `npx vitest run` para confirmar que los tests existentes siguen en verde

---

## 6. TanStack Query UX — useProductsCatalog [vercel-react-best-practices]

> **Contexto**: Al cambiar de página en el catálogo, el grid desaparece mientras carga la nueva página. `keepPreviousData` evita este parpadeo mostrando los datos anteriores con el estado `isFetching`.

- [ ] 6.1 Leer `frontend/src/features/products/hooks/useProductsCatalog.ts` para ver estado actual
- [ ] 6.2 Importar `keepPreviousData` de `@tanstack/react-query`
- [ ] 6.3 Agregar `placeholderData: keepPreviousData` a las opciones del `useQuery` en `useProductsCatalog`
- [ ] 6.4 En `Catalog.tsx` o `ProductGrid.tsx`, verificar que se use `isFetching` (distinto de `isPending`) para mostrar un indicador de carga superpuesto mientras los datos anteriores son visibles
- [ ] 6.5 Correr `npx vitest run features/products/` para confirmar sin regresiones en los hooks

---

## 7. Setup E2E Playwright — Guards de rutas [testing-e2e-playwright]

> **Contexto**: `ProtectedRoute` implementa 3 guards (hydration, auth, roles) pero no hay tests E2E que los verifiquen. Este es el setup inicial de Playwright para el proyecto.

- [ ] 7.1 Instalar Playwright: `cd frontend && npm install -D @playwright/test && npx playwright install chromium`
- [ ] 7.2 Crear `frontend/playwright.config.ts`:
  ```ts
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
- [ ] 7.3 Agregar scripts a `frontend/package.json`:
  ```json
  "e2e": "playwright test",
  "e2e:ui": "playwright test --ui",
  "e2e:debug": "playwright test --debug"
  ```
- [ ] 7.4 Crear `frontend/e2e/helpers/auth.ts` con la función `loginAs(page, role)` que siembra el estado de auth en localStorage usando la clave `food-store-auth` y estructura `{ state: { accessToken, user: { id, email, name, roles }, isAuthenticated, _hasHydrated } }` (patrón de la skill testing-e2e-playwright)
- [ ] 7.5 Crear `frontend/e2e/route-guards.spec.ts` con estos 4 tests:
  - **Test 1**: usuario no autenticado → navegar a `/profile` → debe redirigir a `/login`
  - **Test 2**: usuario no autenticado → navegar a `/admin` → debe redirigir a `/login`
  - **Test 3**: usuario con rol CLIENT → navegar a `/admin/usuarios` (ADMIN-only) → debe redirigir a `/403`
  - **Test 4**: usuario con rol ADMIN → navegar a `/admin/usuarios` → debe renderizar la página (sin redirect)
- [ ] 7.6 Correr `npm run e2e` con el backend levantado y confirmar que los 4 tests pasan
- [ ] 7.7 Agregar `frontend/e2e/` al `.gitignore` para los artifacts de Playwright (`test-results/`, `playwright-report/`); incluir los archivos de test en git

---

## 8. Verificación final [post-change-verification]

- [ ] 8.1 Leer `.agents/skills/post-change-verification/SKILL.md`
- [ ] 8.2 `cd frontend && npx tsc --noEmit` → 0 errores
- [ ] 8.3 `cd frontend && npx vitest run` → todos los tests existentes en verde
- [ ] 8.4 `cd frontend && npm run build` → build exitoso sin warnings críticos
- [ ] 8.5 `cd frontend && npm run dev` → levantar y verificar manualmente:
  - Catálogo carga correctamente (con lazy loading — sin regresión visual)
  - Paginación no parpadea al cambiar de página
  - Redux DevTools muestra `AuthStore` y `CartStore` en el browser
- [ ] 8.6 `cd frontend && npm run e2e` → 4 tests de guards en verde
- [ ] 8.7 Commit: `refactor: apply frontend skills — code splitting, devtools, semantic tokens, ARIA, E2E setup`
