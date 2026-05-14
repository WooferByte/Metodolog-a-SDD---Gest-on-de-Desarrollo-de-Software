## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens semánticos Tailwind v4, `@theme`, animaciones con `@keyframes` y `@starting-style`
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — WCAG 2.1 AA, ARIA, mobile-first, accesibilidad de componentes interactivos
- [ ] 0.3 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — `bundle-dynamic-imports` (React.lazy), `rerender-no-inline-components`, `rendering-conditional-render`
- [ ] 0.4 Leer `.agents/skills/zustand-state-management/README.md` — selectores granulares Zustand v5, evitar suscripción a store completo
- [ ] 0.5 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación Zustand (client state) vs TanStack Query (server state), evitar duplicación
- [ ] 0.6 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — `loginAs()` con `addInitScript`, `page.route` para mock backend, selectores por `data-testid`

## 1. Verificación previa

- [ ] 1.1 Ejecutar `npx vitest run` desde `frontend/` y confirmar que los 275 tests existentes pasan sin cambios
- [ ] 1.2 Revisar `frontend/src/store/types.ts` para confirmar la interfaz `CartItem` (`productId`, `name`, `price`, `quantity`, `image?`, `ingredientes_excluidos: number[]`)
- [ ] 1.3 Verificar que `frontend/src/app/index.css` tiene `@theme` configurado con los tokens semánticos (`--color-primary`, `--color-muted`, `--color-card`, `--color-border`, etc.)

## 2. CartItemRow — visual upgrade

- [ ] 2.1 Aumentar imagen de 80×80 a 96×96 (`w-24 h-24`) en desktop con fallback mantenido; mantener 80×80 en mobile (`sm:w-24 sm:h-24 w-20 h-20`)
- [ ] 2.2 Reemplazar etiquetas de ingredientes excluidos de `Sin: #ID` a `Sin ingrediente` (texto legible) — mantener pill style con `bg-muted text-muted-foreground`
- [ ] 2.3 Agregar descripción corta del producto: si `CartItem` tiene campo `description`, mostrarlo truncado a 1 línea; si no existe el campo, omitir sección (NO agregar al tipo)
- [ ] 2.4 Verificar que el subtotal por ítem (`precio × cantidad`) está visible, alineado a la derecha, con label "Subtotal:" en `text-muted-foreground` y valor en `font-semibold text-foreground`
- [ ] 2.5 Asegurar `hover:border-ring transition-colors` en el card article (ya existe; verificar que funciona correctamente con los tokens actuales)
- [ ] 2.6 Agregar animación de entrada con `@starting-style` (CSS) o clase Tailwind para `opacity` + `translateY`: el ítem entra desde `-8px` con `opacity: 0` y anima a posición normal en `200ms`

## 3. OrderSummary — desglose de costos

- [ ] 3.1 Agregar constante `FREE_DELIVERY_THRESHOLD = 3000` y `DELIVERY_FEE = 500` como constantes locales en `OrderSummary.tsx` con comentario `// TODO: replace with API values in checkout change`
- [ ] 3.2 Implementar lógica: si `totalPrice() >= FREE_DELIVERY_THRESHOLD` → delivery = 0, sino → delivery = `DELIVERY_FEE`
- [ ] 3.3 Agregar fila "Subtotal" al desglose (valor del carrito sin delivery)
- [ ] 3.4 Agregar fila "Envío" con valor calculado (`$0` si gratis, `$500` si no)
- [ ] 3.5 Mostrar badge "Envío gratis" (pill verde con texto pequeño) cuando delivery = 0
- [ ] 3.6 Mostrar barra/texto de progreso "Te faltan $X para envío gratis" cuando delivery > 0 — calcular como `FREE_DELIVERY_THRESHOLD - totalPrice()`
- [ ] 3.7 Actualizar botón CTA para incluir el total en el texto: "Proceder al pago · $X.XXX" o layout con total en botón
- [ ] 3.8 Aumentar padding del botón CTA a `py-3.5` para mayor prominencia visual
- [ ] 3.9 Verificar todos los states ARIA del botón: disabled cuando vacío (`aria-disabled="true"`), enabled con items

## 4. EmptyCart — rediseño food store

- [ ] 4.1 Reemplazar ilustración SVG actual de carrito genérico por una ilustración de food store: opciones son un plato con tenedor/cuchillo, una bandeja vacía, o una caja de pedido abierta — usar `currentColor` y `aria-hidden="true"`
- [ ] 4.2 Actualizar heading: `"Tu carrito está vacío"` (ya existe) → mantener o ajustar tono; agregar un subtexto más cálido como `"¿Qué se te antoja hoy?"`
- [ ] 4.3 Agregar ícono al botón CTA: usar `UtensilsCrossed` o `ChefHat` de `lucide-react` junto al texto "Ver el menú" (cambiar de "Ver productos")
- [ ] 4.4 Verificar que el CTA navega a `/catalog` y tiene focus ring visible para keyboard nav

## 5. CartPage — layout y polish

- [ ] 5.1 Verificar que el grid `grid-cols-1 lg:grid-cols-[1fr_380px]` está implementado — ya existe en la base, confirmar que funciona correctamente
- [ ] 5.2 Asegurar que el `<div>` contenedor de `OrderSummary` tiene clase sticky correcta: en el componente `OrderSummary` confirmar `sticky top-4`
- [ ] 5.3 Agregar `items-start` al grid container para que el sticky funcione correctamente (ya presente; verificar)
- [ ] 5.4 Agregar separador visual entre header y lista de ítems (`border-b border-border mb-6 pb-4` en el header div)
- [ ] 5.5 Verificar responsive: en 375px, 768px, y 1024px+ el layout se comporta correctamente

## 6. CartDrawer — polish visual

- [ ] 6.1 Agregar `aria-live="polite"` al contador de ítems en el header del drawer (ya existe; verificar que el número se anuncia al cambiar)
- [ ] 6.2 Asegurar que el botón "Proceder al pago" en el footer del drawer tiene el mismo estilo prominente que el de CartPage (`py-3` mínimo, `font-semibold`)
- [ ] 6.3 Asegurar que el scroll de la lista de ítems es smooth: `scroll-smooth` o `overscroll-contain` en el contenedor scrollable
- [ ] 6.4 Verificar que el backdrop tiene `transition-opacity duration-300` y que el drawer tiene `transition-transform duration-300 ease-in-out` (ya existe; validar tokens)

## 7. Animaciones CSS

- [ ] 7.1 Verificar que `frontend/src/app/index.css` (o archivo de estilos global) tiene definidos `@keyframes` para `slide-in` y `fade-in` en el bloque `@theme` de Tailwind v4
- [ ] 7.2 Si no existen, agregar los keyframes necesarios: `fade-in` (opacity 0→1), `slide-in-down` (translateY -8px→0 + opacity 0→1)
- [ ] 7.3 Aplicar animación de entrada a CartItemRow: clase que use `@starting-style` o clase de utilidad Tailwind `animate-[slide-in-down_0.2s_ease-out]` al article

## 8. Tests E2E con Playwright

- [ ] 8.1 Verificar que Playwright está instalado en el proyecto: `cat frontend/package.json | grep playwright`; si no está, ejecutar `cd frontend && npm install -D @playwright/test && npx playwright install chromium`
- [ ] 8.2 Verificar que existe `frontend/playwright.config.ts`; si no, crearlo según el template del skill `testing-e2e-playwright`
- [ ] 8.3 Verificar que existe `frontend/e2e/helpers/auth.ts` con la función `loginAs()`; si no, crearlo según el skill
- [ ] 8.4 Crear `frontend/e2e/cart/cart-flow.spec.ts` con los siguientes tests:
  - Test: carrito vacío muestra EmptyCart con CTA a /catalog
  - Test: carrito con ítems muestra lista + OrderSummary con desglose
  - Test: QuantityStepper incrementa y decrementa cantidad correctamente
  - Test: botón "Vaciar carrito" limpia todos los ítems
  - Test: "Proceder al pago" sin auth → redirige a /login con `state.from.pathname === '/checkout'`
  - Test: "Proceder al pago" con auth → navega a /checkout
  - Test: badge "Envío gratis" aparece cuando total >= $3000
- [ ] 8.5 Verificar que los tests pasan: `cd frontend && npx playwright test e2e/cart/cart-flow.spec.ts`

## 9. Verificación final

- [ ] 9.1 Ejecutar `npx vitest run` — todos los 275 tests existentes deben seguir pasando
- [ ] 9.2 Ejecutar `npm run lint` desde `frontend/` — cero errores ESLint
- [ ] 9.3 Ejecutar `npx tsc --noEmit` desde `frontend/` — cero errores TypeScript
- [ ] 9.4 Verificar manualmente en browser a 375px, 768px, y 1280px:
  - [ ] CartPage layout mobile: columna única ✓
  - [ ] CartPage layout desktop: dos columnas con panel sticky ✓
  - [ ] CartItemRow: imagen prominente, personalizaciones legibles, subtotal visible ✓
  - [ ] OrderSummary: desglose subtotal/delivery/total, badge envío gratis ✓
  - [ ] EmptyCart: ilustración food store, CTA con ícono ✓
  - [ ] CartDrawer: slide animation, backdrop fade, footer CTA prominente ✓
- [ ] 9.5 Verificar accesibilidad: navegar con Tab a través del carrito completo — todos los elementos interactivos alcanzables y con focus ring visible
- [ ] 9.6 Leer `.agents/skills/post-change-verification/SKILL.md` y ejecutar el health check completo
