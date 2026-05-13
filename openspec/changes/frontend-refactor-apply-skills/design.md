## Context

El frontend tiene una base sólida (FSD, TypeScript strict, Tailwind v4 con `@theme`, TanStack Query v5, Zustand v5) pero cuatro changes se ejecutaron antes de que se estableciera el protocolo de skills. Los gaps no son fallas funcionales sino ausencias de patrones que las skills exigen.

Estado actual por área:

| Área | Estado actual | Gap |
|------|--------------|-----|
| Code splitting | Todos los pages son imports estáticos en Router.tsx | Bundle único — todos los chunks cargados al inicio |
| Zustand devtools | `create()` sin `devtools` wrapper | No debuggable en Redux DevTools |
| Tokens semánticos | CSS `@theme` correcto; algunos componentes usan colores crudos | `bg-blue-600` en Pagination, posibles raw colors en products |
| ARIA | Spinner de ProtectedRoute correcto; componentes de catálogo sin auditar | Filtros, modal, cards sin atributos de accesibilidad completos |
| TanStack Query UX | Sin `placeholderData` en useProductsCatalog | Parpadeo al cambiar de página |
| Dead code | `withAuth` HOC deprecated exportado desde withAuth.tsx | Dead code confuso para futuros devs |
| E2E | No existe setup de Playwright | Guards de rutas sin cobertura E2E |

## Goals / Non-Goals

**Goals:**
- Code splitting por ruta con `React.lazy` + `Suspense` en Router.tsx
- `devtools` middleware en authStore y cartStore
- Tokens semánticos en todos los componentes de la feature `products/`
- ARIA mínimo viable en componentes de catálogo (roles, labels, live regions)
- `placeholderData: keepPreviousData` en useProductsCatalog
- Setup completo de Playwright con helpers de auth y spec de guards
- Eliminar el HOC `withAuth` deprecated

**Non-Goals:**
- No agregar nuevas páginas ni rutas
- No implementar E2E para flujos aún no existentes (checkout, admin, pagos)
- No instalar Radix UI primitives (no están en las dependencias actuales)
- No migrar a shadcn/ui en este change
- No modificar stores de paymentStore ni uiStore

## Technical Decisions

### Code splitting

Usar `React.lazy()` + `Suspense` a nivel de ruta en Router.tsx. Fallback: spinner con tokens semánticos (igual al spinner del ProtectedRoute). Todas las páginas actuales se convierten a lazy imports.

```tsx
const Catalog = lazy(() => import('@/pages/Catalog'))
const Login   = lazy(() => import('@/pages/Login'))
// ...

<Suspense fallback={<PageSpinner />}>
  <Routes>...</Routes>
</Suspense>
```

El `PageSpinner` reutiliza el markup existente del spinner de ProtectedRoute, extraído a `@/shared/components/ui/Spinner.tsx` para no duplicar.

### Zustand devtools

Wrappear con `devtools()` después del `persist()` — el orden importa en Zustand v5:

```ts
export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(...),
    { name: 'AuthStore' }
  )
)
```

Aplica a authStore y cartStore. paymentStore y uiStore quedan fuera del scope (fueron implementados con skills activas).

### Tokens semánticos en componentes

Regla: ningún componente en `features/products/` debe usar colores de la paleta de Tailwind directamente (ej: `blue-600`, `gray-500`, `green-500`). Todos deben usar los tokens del `@theme`:

| Color crudo | Token semántico |
|-------------|----------------|
| `bg-blue-600` | `bg-primary` |
| `text-gray-500` | `text-muted-foreground` |
| `border-gray-200` | `border-border` |
| `bg-green-100` | `bg-success/10` |
| `text-green-700` | `text-success` |

### ARIA mínimo viable

Para este change se aplican estas reglas de `ui-design-system`:
- Botones sin texto visible: agregar `aria-label`
- Listas de productos: `role="list"` + `role="listitem"` en items
- Modal (ProductDetail): `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Filtros activos: `aria-live="polite"` en la región de resultados
- Loading states: `aria-busy="true"` en el contenedor del grid

### placeholderData para paginación

```ts
import { keepPreviousData } from '@tanstack/react-query'

return useQuery<ProductsApiResponse>({
  // ...
  placeholderData: keepPreviousData,
})
```

Evita que el grid desaparezca al cambiar de página mientras llega la nueva data.

### Playwright setup

- Instalar `@playwright/test` como devDependency
- `playwright.config.ts` en `frontend/` — apunta a `http://localhost:5173`
- `frontend/e2e/helpers/auth.ts` — `loginAs(page, role)` usando localStorage seed (patrón de la skill)
- `frontend/e2e/route-guards.spec.ts` — 4 tests: unauthenticated→/login, CLIENT→/403 en rutas ADMIN, ADMIN→acceso a todo, hydration delay

### Eliminar withAuth HOC

Remover la función `withAuth` de `withAuth.tsx`. Verificar que no haya imports de `withAuth` en el codebase (solo `ProtectedRoute` se usa en Router.tsx).

## Migration Notes

- Todos los cambios son internos — sin cambios de API pública de componentes
- Los tests de vitest existentes no deben romperse
- El spinner extraído (`Spinner.tsx`) es un nuevo archivo pero reutiliza markup existente — no es funcionalidad nueva
