## Context

El change anterior (`frontend-shopping-cart-zustand`, git 4b63561) entregó un carrito completamente funcional: `cartStore` con persistencia en localStorage, `CartItemRow`, `OrderSummary`, `QuantityStepper`, `EmptyCart`, `CartDrawer`, y `CartPage` con layout base. Todos los tests unitarios (275/275) pasan.

Sin embargo, el diseño visual es utilitario: los componentes transmiten funcionalidad pero no emoción. En un e-commerce de food store, el carrito es el último punto de conversión antes del pago — su diseño impacta directamente en la tasa de checkout completado.

**Restricciones:**
- Tailwind v4 únicamente (`@theme` tokens, sin `tailwind.config.ts`)
- Zustand v5 con API `create<T>()()` — sin cambios de lógica
- FSD estricto: Pages → Widgets → Features → Entities → Shared
- TypeScript strict, path alias `@/`
- `CartItem` type inmutable (no agregar campos al store)
- Sin nuevas dependencias npm — usar solo lo instalado

## Goals / Non-Goals

**Goals:**
- Layout dos columnas desktop (ítems izquierda | resumen sticky derecha) en `/cart`
- Cada CartItemRow: imagen 96×96, descripción corta, personalizaciones con nombre real (no ID), subtotal por ítem, animación de entrada
- OrderSummary: desglose subtotal + delivery estimado + total, badge "Envío gratis" si total > $3000, botón checkout con estilo CTA de alta conversión
- EmptyCart: ilustración SVG de food store, mensaje con tono cálido, CTA hacia catálogo con ícono
- CartDrawer: polish — contador animado, scroll smooth, footer CTA más prominente
- Transiciones suaves (`transition-all duration-200`) en modificaciones de ítems
- Tests E2E Playwright: flujo completo agregar → modificar cantidad → proceder al pago
- Responsivo desde 375px hasta 1440px+

**Non-Goals:**
- Cambios en `cartStore.ts` — lógica intacta
- Nuevas features de negocio (cupones, descuentos, selección de dirección)
- Integración con backend — carrito es 100% client-side
- Dark mode changes — los tokens semánticos existentes lo manejan automáticamente
- Cambios en `QuantityStepper` — ya es accesible y responsivo

## Decisions

### D1: Nombres de ingredientes excluidos — mostrar nombre vs. ID

**Problema**: `CartItem.ingredientes_excluidos` es `number[]` (IDs). Mostrar `Sin: #3` no es legible para el usuario.

**Decisión**: En CartItemRow, si no hay un map de ingredientes disponible, mostrar etiquetas genéricas como "Personalización activa" o "Sin ingrediente" en lugar de los IDs crudos. La resolución de nombres requeriría TanStack Query llamando al endpoint `/ingredientes/{id}`, lo que introduce coupling innecesario con el servidor en un componente puramente client-side.

**Alternativas consideradas:**
- Guardar el nombre del ingrediente en `CartItem` al momento de agregar → requiere cambiar el type y el store (fuera de scope)
- Llamar API desde CartItemRow → violaría la separación Zustand (client) / TanStack Query (server)
- **Elegida**: mostrar etiquetas descriptivas sin nombres exactos — correcto para este change; el change de ingredientes resolverá esto cuando esté disponible

### D2: Delivery estimado en OrderSummary

**Problema**: No hay lógica de negocio de delivery en el frontend aún.

**Decisión**: Mostrar delivery fijo de $500 ARS o "Gratis" si el subtotal supera $3000. Esto es un placeholder visual — la lógica real vendrá en el change de checkout. El componente recibe el valor como constante local.

**Alternativas consideradas:**
- Ocultar delivery hasta que llegue el change de checkout → pobre UX, el resumen parece incompleto
- **Elegida**: constante hardcoded con comentario `// TODO: replace with real delivery calculation in checkout change`

### D3: Animaciones con CSS nativo vs. library

**Decisión**: CSS transitions de Tailwind v4 (`transition-all duration-200 ease-in-out`) + `@starting-style` para animación de entrada de nuevos CartItemRow. Sin Framer Motion ni react-spring — mantiene el bundle pequeño.

**Para CartItemRow entry animation**: usar la técnica `@starting-style` de CSS (ya en Tailwind v4 con `@keyframes` en `@theme`). El ítem entra con `opacity: 0; transform: translateY(-8px)` y anima a estado visible.

### D4: Sticky panel en OrderSummary

**Decisión**: `sticky top-4` en el contenedor del panel. En mobile el layout es columna única — el panel va después de la lista de ítems, sin sticky (no tiene sentido en scroll vertical continuo). En desktop (`lg:`) el grid de dos columnas activa el sticky.

**Alternativa**: `position: fixed` → requiere calcular offsets, dificulta accesibilidad. Sticky es más natural.

### D5: Badge "Envío gratis" — umbral $3000

**Decisión**: Constante `FREE_DELIVERY_THRESHOLD = 3000` en `OrderSummary.tsx`. Si `totalPrice() >= 3000`, mostrar badge verde "Envío gratis" y delivery = $0. Si no, mostrar barra de progreso visual con "Te faltan $X para envío gratis".

### D6: Tests E2E — alcance del change

**Decisión**: Tests en `frontend/e2e/cart/cart-flow.spec.ts` con `page.route` para mockear backend (no depende de FastAPI corriendo). Flujos a cubrir:
1. Carrito vacío → muestra EmptyCart → CTA lleva a /catalog
2. Carrito con ítems → layout correcto, stepper funciona, subtotales calculados
3. Botón "Proceder al pago" sin auth → redirige a /login con state correcto
4. Botón "Proceder al pago" con auth → navega a /checkout
5. "Vaciar carrito" borra todos los ítems y muestra EmptyCart

El helper `loginAs()` del skill `testing-e2e-playwright` se usa para seedear auth state.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Nombres de ingredientes no resueltos (IDs crudos) | Etiquetas genéricas + comentario de deuda técnica |
| Delivery hardcoded puede confundir al usuario final | Texto "estimado" en el label + placeholder comentado |
| `@starting-style` tiene soporte limitado en Safari < 17.4 | Fallback graceful — ítem aparece sin animación |
| CartDrawer y CartPage comparten mucho código de display | Aceptable — son contextos distintos (drawer vs. página completa). DRY optimo sería un componente `CartItemList` compartido — considerar en siguiente change |
| Tests E2E requieren Playwright instalado | Documentado en tasks.md con paso de instalación explícito |

## Migration Plan

1. Modificar componentes existentes uno a uno — no hay breaking changes
2. Cada componente modificado mantiene su interfaz de props existente
3. CartPage no cambia props — solo layout y estilos
4. Los tests unitarios existentes (275/275) deben seguir pasando sin cambios
5. Los tests E2E son nuevos — no reemplazan ningún test existente

## Open Questions

- **Q1**: ¿El umbral de envío gratis ($3000) es el valor correcto según el spec del negocio?
  - **Respuesta provisional**: $3000 como placeholder, comentado con TODO. No bloquea el change.
- **Q2**: ¿CartItemList debería extraerse como componente compartido entre CartPage y CartDrawer?
  - **Respuesta provisional**: No en este change — la deuda es tolerable. Agregar a backlog.
