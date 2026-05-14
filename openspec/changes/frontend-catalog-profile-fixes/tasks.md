## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — Tailwind v4 tokens semánticos, clases responsive mobile-first, patrón `hidden md:block`, separadores visuales y `accent-primary` en filtros
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — accesibilidad WCAG AA, ARIA en checkboxes (`aria-label`, `fieldset/legend`), foco visible, jerarquía tipográfica
- [ ] 0.3 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación Zustand (estado cliente) vs TanStack Query (estado servidor); confirmar que el fix no duplica estado servidor en Zustand
- [ ] 0.4 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — `rerender-no-inline-components`, `rendering-conditional-render` (ternary no &&), evitar waterfalls en el layout del catálogo
- [ ] 0.5 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — patrón de mock backend `page.route`, pattern `data-testid="toast"`, verificación de toasts con string vs crash
- [ ] 0.6 Leer `.agents/skills/jwt-security/SKILL.md` — confirmar que el fix del interceptor Axios no altera el flujo de refresh token ni el manejo de 401

## 1. BUG 1 — Toast string normalisation (axios.ts + ToastContainer.tsx)

- [ ] 1.1 En `frontend/src/shared/api/axios.ts`, agregar la función `safeString(value: unknown): string | undefined` antes del interceptor de respuesta. Implementar según D-1 del design: si `typeof value === 'string'` retornar directo; si es objeto con propiedad `detail`, recursar sobre ella; sino `JSON.stringify(value)`; si null/undefined retornar `undefined`.
- [ ] 1.2 En el mismo archivo, reemplazar la línea `const rfcDetail = (error.response.data as Partial<ApiError>)?.detail` por `const rfcDetail = safeString((error.response.data as Partial<ApiError>)?.detail)` para garantizar que `rfcDetail` siempre sea `string | undefined`.
- [ ] 1.3 En `frontend/src/shared/components/ToastContainer.tsx`, en el componente `ToastItem`, cambiar `{toast.message}` por `{String(toast.message)}` dentro del `<p>` — belt-and-suspenders según D-1.
- [ ] 1.4 Actualizar (o agregar) test en `frontend/src/shared/components/__tests__/ToastContainer.test.tsx` con caso: dado un toast cuyo `message` es un objeto `{ detail: 'Error' }`, el componente NO debe lanzar error y debe renderizar algún string legible.
- [ ] 1.5 Verificar que los tests existentes de `axios.ts` (si existen en `frontend/src/shared/api/__tests__/`) siguen pasando con `npx vitest run`.

## 2. BUG 2 — Eliminar comparación client-side de passwords (ChangePasswordForm.tsx)

- [ ] 2.1 En `frontend/src/features/profile/components/ChangePasswordForm.tsx`, en la función `validate()`, eliminar el bloque `else if (nuevaPassword === passwordActual) { newErrors.nuevaPassword = 'La nueva contraseña debe ser diferente a la actual.' }` completo. Mantener solo: campo requerido y longitud mínima 8 caracteres para ambos campos.
- [ ] 2.2 Verificar que el comentario del JSDoc en el componente ya refleja que "La validación de contraseña actual incorrecta es responsabilidad del backend (400 vía toast del interceptor)." Actualizar si no es así.
- [ ] 2.3 En `frontend/src/features/profile/__tests__/ChangePasswordForm.test.tsx`, eliminar o actualizar el test case que verifica el error "La nueva contraseña debe ser diferente a la actual." — reemplazarlo por un test que confirma que con strings iguales el componente llama a `mutate()` y NO muestra error de validación client-side.

## 3. BUG 3 — Responsive layout del catálogo (Catalog.tsx + FilterBar.tsx)

- [ ] 3.1 En `frontend/src/pages/Catalog.tsx`, sacar el bloque `{/* Mobile filter trigger */}` fuera de la `<div className="grid ...">` y ubicarlo como fila independiente (hermano anterior al grid). Este bloque debe contener solo el botón hamburger visible en mobile (`md:hidden`) y el `AppliedFilters`.
- [ ] 3.2 En `Catalog.tsx`, envolver el `<div className="md:col-span-1">` que contiene `FilterBar` con `hidden md:block md:col-span-1` para que en mobile no ocupe espacio en el grid. El `FilterBar` en desktop seguirá siendo el sidebar del grid.
- [ ] 3.3 En `frontend/src/features/products/components/FilterBar.tsx`, mover el botón hamburger mobile (`md:hidden`) fuera del componente o aceptarlo como `prop` externo — el orquestador en `Catalog.tsx` es quien controla la visibilidad. Simplificar `FilterBar` para que en mobile solo reciba `isOpen` como prop y renderice el `<aside>` condicional con `isOpen ? 'block' : 'hidden'`.
- [ ] 3.4 En `FilterBar.tsx`, confirmar que el overlay backdrop `fixed inset-0 bg-black/25 z-40` tiene `z-index` menor que el panel del filtro para no bloquear el panel.
- [ ] 3.5 Ajustar el `<aside>` de `FilterBar.tsx` para que en mobile use `fixed top-0 left-0 h-full w-72 bg-card z-50 overflow-y-auto shadow-lg` cuando está abierto — overlay lateral en vez de layout flow.
- [ ] 3.6 Verificar que el `ProductGrid` en `Catalog.tsx` usa `md:col-span-3` y en mobile (con filter col oculto) el grid se reconfigura a `grid-cols-1` correctamente.

## 4. PROBLEMA 4 — Diseño visual del panel de filtros (CategoryFilter.tsx + AllergenFilter.tsx + FilterBar.tsx)

- [ ] 4.1 En `frontend/src/features/products/components/FilterBar.tsx`, entre cada sección de filtro (`SearchInput`, `CategoryFilter`, `AllergenFilter`), agregar `<hr className="border-border" />` como separador visual. Reemplazar `space-y-6` por `divide-y divide-border` en el `<aside>` o manejar padding `py-4` en cada sección.
- [ ] 4.2 En `frontend/src/features/products/components/CategoryFilter.tsx`, cambiar el `<label>` que actúa como heading de sección por `<h3 className="text-sm font-semibold text-foreground mb-3">Categories</h3>`. Verificar que los checkboxes de parent categories tienen `accent-primary` en la clase `className` del `<input type="checkbox">`. Agregar `focus:ring-2 focus:ring-ring focus:ring-offset-1` a los inputs.
- [ ] 4.3 En `frontend/src/features/products/components/AllergenFilter.tsx`, confirmar que el `<legend>` del `<fieldset>` usa `text-sm font-semibold text-foreground`. Agregar `accent-primary` a los checkbox inputs. Agregar `focus:ring-2 focus:ring-ring focus:ring-offset-1` a los inputs. Verificar que `aria-label` de cada checkbox incluye el count: `Exclude ${allergen.nombre} (found in ${allergen.count} product${allergen.count !== 1 ? 's' : ''})`.
- [ ] 4.4 En `FilterBar.tsx`, el botón "Clear All Filters" debe usar clases de estado hover consistentes con el design system: `hover:bg-muted/50 hover:text-foreground` en lugar de texto genérico. Confirmar que usa `border border-border`.
- [ ] 4.5 Verificar visualmente (o mediante snapshot test si existe) que el resultado aplica jerarquía: heading de sección → separador → checkboxes con etiquetas — sin clases hardcodeadas de colores (no usar `#hex`, `rgb()`, o clases fuera de los tokens `@theme`).

## 5. Testing y verificación

- [ ] 5.1 Ejecutar `cd frontend && npx vitest run` — todos los tests deben pasar (0 failures). Si algún test falla por los cambios de BUG 1, 2 o 3, corregirlo antes de continuar.
- [ ] 5.2 Ejecutar `cd frontend && npm run lint` — 0 errores de ESLint/TypeScript.
- [ ] 5.3 Ejecutar `cd frontend && npx tsc --noEmit` — 0 errores de tipo.
- [ ] 5.4 Smoke test manual BUG 1: Con backend corriendo, ir a `/profile`, intentar cambiar password con contraseña actual incorrecta → verificar que aparece toast con texto legible (no crash, no `[object Object]`).
- [ ] 5.5 Smoke test manual BUG 2: Con backend corriendo, ir a `/profile`, ingresar la misma string en ambos campos de contraseña con longitud ≥ 8 → verificar que el formulario permite el submit (sin error client-side) y el backend responde con toast de error.
- [ ] 5.6 Smoke test manual BUG 3: Abrir `/catalog` en viewport 375px → verificar que no hay espacio vacío encima de los productos y que el botón de filtro aparece sobre los productos.
- [ ] 5.7 Smoke test manual PROBLEMA 4: Abrir panel de filtros en desktop → verificar separadores visuales entre secciones, heading tipográfico, checkboxes con accent color del theme.
