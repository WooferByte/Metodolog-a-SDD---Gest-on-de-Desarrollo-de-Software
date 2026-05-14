## Why

El carrito funciona correctamente (lógica Zustand completa con 275/275 tests) pero carece de la identidad visual y experiencia sensorial que una food store real requiere. Los componentes existentes son funcionales pero minimalistas: no transmiten apetito, no guían emocionalmente al usuario hacia el checkout, y no están optimizados para conversión. Este change transforma el carrito de "funcional" a "deseable".

## What Changes

- **CartPage** (`/cart`): rediseño con layout dos columnas desktop (ítems izquierda, resumen sticky derecha) y stack vertical mobile; transiciones suaves al agregar/eliminar ítems
- **CartItemRow**: imagen más prominente (96×96 desktop), descripción corta del producto visible, personalizaciones activas con etiquetas legibles (nombre, no ID), subtotal por ítem con jerarquía visual clara, animación de entrada con `@starting-style`
- **OrderSummary**: desglose completo (subtotal de productos + delivery estimado + total), botón checkout prominente con estilo de CTA de conversión, badge de "Envío gratis" si supera umbral
- **EmptyCart**: rediseño con ilustración de food/carrito, mensaje emotivo con CTA destacado hacia catálogo
- **CartDrawer**: polish visual — header con contador animado, footer con CTA más visible, scroll smooth en lista de ítems
- **Animaciones**: `transition-all duration-200` en agregar/quitar ítems, animación `slide-in` en CartItemRow nuevo, transición fade en estado vacío
- **Tests E2E**: suite Playwright para flujo completo carrito → checkout (agregar, modificar cantidad, proceder al pago)

## Capabilities

### New Capabilities

- `cart-page-layout`: Layout responsive de dos columnas para la página /cart con panel de resumen sticky
- `cart-item-visual`: Presentación visual enriquecida de cada ítem (imagen prominente, descripción, personalizaciones legibles, subtotal)
- `order-summary-breakdown`: Desglose de costos en panel de resumen (subtotal + delivery + total) con badge de envío gratis
- `cart-empty-state`: Estado vacío con diseño emocional orientado a food store
- `cart-animations`: Transiciones suaves al modificar ítems del carrito

### Modified Capabilities

<!-- No hay cambios de requisitos en specs existentes — los cambios son puramente visuales/UX sobre la lógica ya implementada -->

## Impact

- **Archivos modificados**: `frontend/src/pages/CartPage.tsx`, `frontend/src/features/cart/components/CartItemRow.tsx`, `frontend/src/features/cart/components/OrderSummary.tsx`, `frontend/src/features/cart/components/EmptyCart.tsx`, `frontend/src/widgets/CartDrawer/CartDrawer.tsx`
- **Archivos nuevos**: `frontend/e2e/cart/cart-flow.spec.ts`
- **Dependencias**: Sin cambios — usa Tailwind v4, lucide-react, Zustand v5 existentes
- **CartItem type**: sin cambios — `productId`, `name`, `price`, `quantity`, `image?`, `ingredientes_excluidos: number[]` se mantienen igual
- **cartStore**: sin cambios de lógica — solo los componentes visuales se actualizan
- **No hay cambios de backend**: carrito es 100% client-side (Zustand + localStorage)
