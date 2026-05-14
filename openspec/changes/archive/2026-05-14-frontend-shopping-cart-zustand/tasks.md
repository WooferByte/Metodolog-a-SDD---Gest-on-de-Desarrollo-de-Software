# Tasks: frontend-shopping-cart-zustand

## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens semánticos `@theme`, variantes CVA, responsive mobile-first para CartPage y CartDrawer
- [ ] 0.2 Leer `.agents/skills/zustand-state-management/README.md` — patrón `devtools(persist(...))`, selectores granulares, `create<T>()()` double parentheses para Zustand v5
- [ ] 0.3 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación Zustand (estado cliente) vs TanStack Query (estado servidor), evitar duplicación
- [ ] 0.4 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — `bundle-dynamic-imports`, `rerender-derived-state`, `rerender-no-inline-components`, `client-localstorage-schema`
- [ ] 0.5 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — `addInitScript` para auth state, `page.route` para mocks, estructura `e2e/cart/`

---

## 1. Auditoría y hardening del store existente

- [ ] 1.1 Leer `frontend/src/store/types.ts` — verificar tipo de `ingredientes_excluidos`
- [ ] 1.2 Si `ingredientes_excluidos` es `string[]`, actualizar a `number[]` en `CartItem` (alinear con backend `INTEGER[]` y RN-CR04/05)
- [ ] 1.3 Leer `frontend/src/store/cartStore.ts` — verificar orden de middleware `devtools(persist(...))` y que `updateQuantity` elimina el ítem cuando `quantity <= 0`
- [ ] 1.4 Leer `frontend/src/store/uiStore.ts` — entender estructura actual del UIStore
- [ ] 1.5 Agregar a `UIStore` interface en `types.ts`: `cartDrawerOpen: boolean`, `toggleCartDrawer: () => void`, `setCartDrawerOpen: (open: boolean) => void`
- [ ] 1.6 Implementar los nuevos campos en `frontend/src/store/uiStore.ts` con estado inicial `cartDrawerOpen: false`
- [ ] 1.7 Verificar que los tests existentes de cartStore en `store/__tests__/cartStore.test.ts` siguen pasando — corregir si algo se rompe por el cambio de tipo

---

## 2. Feature cart — tipos y hooks

- [ ] 2.1 Crear `frontend/src/features/cart/types/index.ts` — exportar `CartUIItem` (extends `CartItem` con helpers de display si se necesitan)
- [ ] 2.2 Crear `frontend/src/features/cart/hooks/useCart.ts`:
  ```ts
  // Selectores granulares — NUNCA subscribir al store completo
  const items = useCartStore((s) => s.items)
  const totalItems = useCartStore((s) => s.totalItems())
  const totalPrice = useCartStore((s) => s.totalPrice())
  const isEmpty = items.length === 0
  return { items, totalItems, totalPrice, isEmpty }
  ```
- [ ] 2.3 Crear `frontend/src/features/cart/hooks/index.ts` — re-exportar `useCart`
- [ ] 2.4 Crear test `frontend/src/features/cart/__tests__/useCart.test.ts` — verificar que `isEmpty` es `true` con carrito vacío, `false` con ítems; que `totalPrice` suma correctamente

---

## 3. Componente QuantityStepper

- [ ] 3.1 Crear `frontend/src/features/cart/components/QuantityStepper.tsx`:
  - Props: `value: number`, `min?: number` (default 1), `max?: number` (default 99), `onChange: (v: number) => void`, `productName: string`
  - ARIA: `role="group"` con `aria-label="Cantidad de {productName}"`, botones con `aria-label`, input con `aria-label` y `type="number"`
  - Estilos: `bg-secondary`, `text-secondary-foreground`, `border-border` — cero colores crudos
  - En `value === min (1)`: botón decrement muestra ícono de papelera con tooltip "Eliminar" y llama `onChange(0)` — el padre decide si remover
- [ ] 3.2 Crear test `frontend/src/features/cart/__tests__/QuantityStepper.test.tsx`:
  - Renderiza con `value=2`, hace click en `+`, verifica que `onChange(3)` fue llamado
  - Con `value=1`, click en `-`, verifica que `onChange(0)` fue llamado
  - Verifica atributos ARIA presentes

---

## 4. Componente CartItemRow

- [ ] 4.1 Crear `frontend/src/features/cart/components/CartItemRow.tsx`:
  - Props: `item: CartItem`, `onQuantityChange: (productId: string, qty: number) => void`, `onRemove: (productId: string) => void`
  - Layout mobile: imagen a la izquierda (w-20 h-20), contenido a la derecha en columna
  - Layout desktop (sm+): flex-row con imagen 80px, nombre+precio, stepper, botón eliminar
  - Nombre: `text-base font-semibold text-foreground`
  - Precio: `text-lg font-bold text-primary`
  - Ingredientes excluidos: pills con `text-xs text-muted-foreground bg-muted rounded px-2 py-0.5`, texto "Sin: {id}" o nombre si disponible
  - Imagen: `loading="lazy"` con fallback SVG en `onError`
  - Botón eliminar: `aria-label="Eliminar {item.name} del carrito"`, ícono `Trash2` de lucide-react
  - Wrapper: `<article role="article" aria-label="Producto: {item.name}">`
  - Cero colores crudos — solo tokens semánticos
- [ ] 4.2 Crear test `frontend/src/features/cart/__tests__/CartItemRow.test.tsx`:
  - Renderiza con un `CartItem` de prueba — verifica nombre, precio, cantidad visibles
  - Simula click en `+` del stepper → verifica que `onQuantityChange` fue llamado con nuevo valor
  - Simula click en eliminar → verifica que `onRemove` fue llamado con `productId`
  - Verifica `aria-label` correcto en el article

---

## 5. Componente EmptyCart

- [ ] 5.1 Crear `frontend/src/features/cart/components/EmptyCart.tsx`:
  - SVG ilustración inline con `aria-hidden="true"` (carrito vacío, estilo food-store)
  - `<h2>Tu carrito está vacío</h2>` con clases `text-xl font-semibold text-foreground`
  - Subtexto con `text-muted-foreground`
  - CTA: `<Link to="/catalog">` con apariencia de botón `bg-primary text-primary-foreground`
  - Centrado vertical y horizontalmente: `flex flex-col items-center justify-center gap-6 py-16`

---

## 6. Componente OrderSummary

- [ ] 6.1 Crear `frontend/src/features/cart/components/OrderSummary.tsx`:
  - Usa selectores granulares: `useCartStore((s) => s.totalItems())` y `useCartStore((s) => s.totalPrice())`
  - Usa `useAuthStore((s) => s.isAuthenticated)` para comportamiento del CTA
  - Muestra: "N producto(s)", subtotal con `Intl.NumberFormat`, botón CTA
  - CTA: si autenticado → `<Link to="/checkout">` (cuando exista), si no → `<Link to="/login" state={{ from: '/checkout' }}>`
  - CTA disabled cuando `totalItems() === 0`
  - Styling: `bg-card border border-border rounded-lg p-6`, heading `text-lg font-semibold`
  - Botón CTA: `w-full bg-primary text-primary-foreground` con hover state
- [ ] 6.2 Crear test `frontend/src/features/cart/__tests__/OrderSummary.test.tsx`:
  - Mock `useCartStore` con 2 ítems → verifica que muestra "2 productos" y precio correcto
  - Con carrito vacío → verifica que botón CTA está `disabled`

---

## 7. Componente CartItemRow + index

- [ ] 7.1 Crear `frontend/src/features/cart/components/index.ts`:
  ```ts
  export { CartItemRow } from './CartItemRow'
  export { QuantityStepper } from './QuantityStepper'
  export { OrderSummary } from './OrderSummary'
  export { EmptyCart } from './EmptyCart'
  ```

---

## 8. Widget CartDrawer

- [ ] 8.1 Crear `frontend/src/widgets/CartDrawer/CartDrawer.tsx`:
  - Lee `cartDrawerOpen` y `setCartDrawerOpen` de `useUIStore`
  - `role="dialog"` `aria-modal="true"` `aria-label="Carrito de compras"`
  - Cierra con Escape key: `useEffect` con `keydown` listener
  - Cierra con click en backdrop
  - Animación CSS: `transition-transform duration-300`, `translate-x-full` cerrado, `translate-x-0` abierto
  - Ancho: `w-full sm:w-[420px]`, siempre a la derecha: `fixed inset-y-0 right-0`
  - Contenido: header con título + botón cerrar, área scrollable con `CartItemRow` × N, footer con `OrderSummary`
  - Botón cerrar: `aria-label="Cerrar carrito"`, ícono `X` de lucide-react
  - **Focus trap**: al abrir, focus va al botón cerrar; al cerrar, focus vuelve al trigger (CartIcon)
  - Backdrop: `fixed inset-0 bg-foreground/40 z-40 sm:block hidden` (solo en mobile)
  - Acciones del carrito: llama `useCartStore` actions directamente
- [ ] 8.2 Crear `frontend/src/widgets/CartDrawer/index.ts`:
  ```ts
  export { CartDrawer } from './CartDrawer'
  ```
- [ ] 8.3 Crear test `frontend/src/widgets/CartDrawer/__tests__/CartDrawer.test.tsx`:
  - Renderiza sin errores cuando `cartDrawerOpen = false`
  - Con `cartDrawerOpen = true`: verifica role="dialog" y aria-modal="true"
  - Simula click en backdrop → verifica que `setCartDrawerOpen(false)` fue llamado

---

## 9. Modificación del Navbar — CartIcon con badge

- [ ] 9.1 Leer `frontend/src/shared/components/Navbar.tsx` completo antes de modificar
- [ ] 9.2 Modificar `Navbar.tsx`:
  - Importar `ShoppingCart` de `lucide-react`
  - Importar `useCartStore` desde `@/store`
  - Importar `useUIStore` desde `@/store`
  - Agregar selector granular: `const cartCount = useCartStore((s) => s.totalItems())`
  - Agregar `toggleCartDrawer` de `useUIStore`
  - Agregar botón CartIcon en la sección derecha (antes del theme toggle):
    ```tsx
    <button
      onClick={toggleCartDrawer}
      aria-label={`Carrito, ${cartCount} producto${cartCount !== 1 ? 's' : ''}`}
      className="relative p-1.5 rounded-md text-gray-300 hover:text-white hover:bg-gray-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
    >
      <ShoppingCart className="h-5 w-5" aria-hidden="true" />
      {cartCount > 0 && (
        <span
          aria-live="polite"
          aria-atomic="true"
          className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-destructive text-destructive-foreground text-xs flex items-center justify-center font-bold"
        >
          {cartCount > 99 ? '99+' : cartCount}
        </span>
      )}
    </button>
    ```
  - CartDrawer se renderiza en `App.tsx` a nivel global — Navbar solo controla el trigger
- [ ] 9.3 No modificar ningún otro comportamiento de Navbar (auth, theme, sidebar)

---

## 10. CartPage

- [ ] 10.1 Crear `frontend/src/pages/CartPage.tsx`:
  - Importaciones con `@/` path alias
  - Layout: `<main>` con heading `<h1>Mi carrito</h1>`
  - Botón "Vaciar carrito" (solo visible cuando `items.length > 0`): llama `clearCart()`
  - Botón con confirmación implícita (sin modal — click directo es suficiente para MVP)
  - Lista de ítems: mapea `items` → `<CartItemRow>` con handlers conectados a `removeItem` y `updateQuantity`
  - Panel derecho (desktop): `<OrderSummary>`
  - Estado vacío: `<EmptyCart>` cuando `items.length === 0`
  - Layout desktop: `grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-8`
  - Layout mobile: columna única, `<OrderSummary>` debajo de la lista
  - Cero `useState` para lógica de carrito — todo via `useCartStore`
  - Accesibilidad: `<main>` con `aria-label="Carrito de compras"`, heading h1
- [ ] 10.2 **No** crear CartPage como componente interno — es una página FSD nivel `pages/`

---

## 11. Modificación del Router — reemplazar placeholder

- [ ] 11.1 Leer `frontend/src/app/Router.tsx`
- [ ] 11.2 Agregar import lazy:
  ```ts
  const CartPage = lazy(() => import('@/pages/CartPage'))
  ```
- [ ] 11.3 Reemplazar `<Route path="/cart" element={<Admin />} />` con `<Route path="/cart" element={<CartPage />} />`
- [ ] 11.4 Verificar que la ruta sigue dentro del ProtectedRoute para `['CLIENT', 'ADMIN']`

---

## 12. Montar CartDrawer globalmente

- [ ] 12.1 Leer `frontend/src/app/App.tsx`
- [ ] 12.2 Importar `CartDrawer` lazy:
  ```ts
  const CartDrawer = lazy(() => import('@/widgets/CartDrawer').then(m => ({ default: m.CartDrawer })))
  ```
- [ ] 12.3 Renderizar `<CartDrawer />` en `App.tsx` fuera del `<Routes>` pero dentro del `<BrowserRouter>` / layout, en el nivel donde puede cubrir toda la pantalla

---

## 13. Tokens de color — verificar app.css

- [ ] 13.1 Leer el archivo CSS principal del frontend (buscar en `src/app/`, `src/index.css`, o `src/app/app.css`)
- [ ] 13.2 Verificar que `--color-success` está definido (usado en ProductCard y CartPage)
- [ ] 13.3 Si no existe `--color-success`, agregar en `@theme`:
  ```css
  --color-success: oklch(55% 0.18 145);
  --color-success-foreground: oklch(98% 0.01 145);
  ```
- [ ] 13.4 Verificar que `--color-destructive` existe (para badge del carrito)
- [ ] 13.5 Agregar tokens específicos del carrito si no existen (ver design.md sección "Food Store palette additions")

---

## 14. Tests E2E con Playwright

- [ ] 14.1 Verificar que Playwright está instalado: `ls frontend/playwright.config.ts` y `ls frontend/e2e/`
- [ ] 14.2 Si no existe `playwright.config.ts`, crearlo según el patrón de `.agents/skills/testing-e2e-playwright/SKILL.md`
- [ ] 14.3 Si no existe `frontend/e2e/helpers/auth.ts`, crearlo con `loginAs()` y `logout()` según el patrón del skill
- [ ] 14.4 Crear `frontend/e2e/cart/cart-flows.spec.ts`:

  ```ts
  // Tests a implementar:
  // 1. add item via cartStore state → navigate to /cart → assert item visible
  // 2. Quantity increment: click '+' → assert quantity updated
  // 3. Quantity decrement from 2 to 1: click '-' → assert quantity is 1 (not removed)
  // 4. Remove item: click trash → assert item gone
  // 5. Clear cart: click "Vaciar carrito" → assert empty state
  // 6. Persist across reload: set localStorage state → reload → assert items
  // 7. Empty state: empty cart → navigate to /cart → assert EmptyCart rendered
  // 8. Checkout CTA unauthenticated: no session → click CTA → assert redirect to /login
  // 9. Navbar badge: set cart with 3 items in localStorage → reload → assert badge shows "3"
  ```

  Para seedear estado del carrito sin UI (igual que auth):
  ```ts
  await page.addInitScript(({ key, value }) => {
    localStorage.setItem(key, JSON.stringify(value))
  }, {
    key: 'food-store-cart',
    value: {
      state: { items: [{ productId: 'p1', name: 'Pizza', price: 10.99, quantity: 2 }] },
      version: 0,
    },
  })
  ```

---

## 15. Verificación de calidad

- [ ] 15.1 Correr tests unitarios:
  ```bash
  cd frontend && npx vitest run src/features/cart src/widgets/CartDrawer src/store/__tests__/cartStore
  ```
  Verificar que todos pasan — cobertura ≥ 40% en archivos del change

- [ ] 15.2 Correr TypeScript check:
  ```bash
  cd frontend && npx tsc --noEmit
  ```
  Cero errores de tipos

- [ ] 15.3 Correr linter:
  ```bash
  cd frontend && npm run lint
  ```
  Cero warnings ni errores

- [ ] 15.4 Verificar que tests existentes NO se rompieron:
  ```bash
  cd frontend && npx vitest run
  ```

- [ ] 15.5 Correr E2E (requiere `npm run dev` corriendo):
  ```bash
  cd frontend && npx playwright test e2e/cart/cart-flows.spec.ts
  ```

---

## 16. Checklist pre-commit (frontend-specific)

- [ ] 16.1 ¿Cero colores crudos en todos los componentes nuevos? Solo tokens semánticos `@theme`
- [ ] 16.2 ¿Cero `useState` donde `useCartStore` aplica?
- [ ] 16.3 ¿`React.lazy + Suspense` aplicados a CartPage y CartDrawer?
- [ ] 16.4 ¿ARIA completo: role, aria-label, aria-live en todos los componentes interactivos?
- [ ] 16.5 ¿Responsive mobile + desktop verificado (al menos inspeccionado en browser)?
- [ ] 16.6 ¿`zustand devtools(persist(...))` — orden correcto en cartStore?
- [ ] 16.7 ¿Imports usando `@/` path alias en todos los archivos nuevos?
- [ ] 16.8 ¿`ingredientes_excluidos` tipado como `number[]`?
- [ ] 16.9 ¿`CartDrawer` en `widgets/` layer, no en `features/` ni `shared/`?
- [ ] 16.10 ¿Selectores granulares — ningún componente subscribe al store completo?

---

## Orden de implementación recomendado

```
Task 1 (store audit)
  → Task 2 (tipos y hooks)
  → Task 3 (QuantityStepper)
  → Task 4 (CartItemRow)
  → Task 5 (EmptyCart)
  → Task 6 (OrderSummary)
  → Task 7 (index exports)
  → Task 8 (CartDrawer widget)
  → Task 9 (Navbar CartIcon)
  → Task 10 (CartPage)
  → Task 11 (Router update)
  → Task 12 (App.tsx CartDrawer mount)
  → Task 13 (tokens CSS)
  → Task 14 (E2E tests)
  → Task 15 (quality check)
  → Task 16 (pre-commit checklist)
```
