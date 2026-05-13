## Why

Cuatro changes de frontend fueron implementados sin cargar las skills de diseño y calidad correspondientes (`tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `frontend-state-management`, `zustand-state-management`, `testing-e2e-playwright`). El resultado es código funcional pero con gaps concretos: sin code splitting en el router, stores de Zustand sin `devtools`, colores crudos en lugar de tokens semánticos en componentes de productos, y sin cobertura E2E para los guards de rutas. Este change cierra esos gaps retroactivamente.

## What Changes

- `frontend/src/app/Router.tsx` — convertir imports estáticos a `React.lazy()` + `Suspense` para code splitting por ruta
- `frontend/src/store/authStore.ts` — agregar middleware `devtools` de Zustand
- `frontend/src/store/cartStore.ts` — agregar middleware `devtools` de Zustand
- `frontend/src/shared/routing/withAuth.tsx` — eliminar HOC `withAuth` deprecated (dead code)
- `frontend/src/features/products/components/Pagination.tsx` — reemplazar `bg-blue-600` con token semántico `bg-primary`
- `frontend/src/features/products/components/*.tsx` — auditar y reemplazar colores crudos con tokens semánticos; mejorar atributos ARIA donde falten
- `frontend/src/features/products/hooks/useProductsCatalog.ts` — agregar `placeholderData: keepPreviousData` para UX de paginación
- `frontend/e2e/` — crear setup Playwright + tests E2E para guards de rutas (ProtectedRoute)

## Capabilities

### New Capabilities
- `frontend-e2e-setup`: Configuración de Playwright para el proyecto frontend — `playwright.config.ts`, `e2e/helpers/auth.ts`, y primer spec de guards de rutas.

### Modified Capabilities
_(ninguna — no cambian los requisitos funcionales, solo la calidad de implementación)_

## Impact

- Sin cambios de comportamiento observable para el usuario final
- Sin cambios de API ni de contratos de datos
- Sin páginas nuevas ni rutas nuevas
- Tests unitarios existentes (vitest) deben seguir en verde
- Se agrega nueva suite de tests E2E (Playwright) — no reemplaza vitest
