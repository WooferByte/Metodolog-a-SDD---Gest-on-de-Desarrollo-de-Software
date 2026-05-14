# Design: frontend-shopping-cart-zustand

## Architecture Overview

This change creates the cart UI layer on top of the existing `cartStore`. It introduces:

1. A new FSD feature: `features/cart/`
2. The first widget in `widgets/`: `CartDrawer`
3. A new page: `pages/CartPage.tsx`
4. Modifications to two shared components: `Navbar.tsx` and `Router.tsx`

All state is read from/written to `useCartStore` and `useUIStore`. No new stores are created.

---

## FSD Layer Map

```
pages/
  CartPage.tsx                      ← lazy-loaded, route /cart

widgets/
  CartDrawer/
    index.ts
    CartDrawer.tsx                  ← slide-in drawer, right side
    CartDrawer.test.tsx

features/
  cart/
    components/
      CartItemRow.tsx               ← single item: image, name, stepper, personalization, remove
      CartItemRow.test.tsx
      OrderSummary.tsx              ← subtotal, item count, CTA
      OrderSummary.test.tsx
      EmptyCart.tsx                 ← empty state illustration + CTA
      EmptyCart.test.tsx
      QuantityStepper.tsx           ← accessible +/- stepper component
      QuantityStepper.test.tsx
      index.ts
    hooks/
      useCart.ts                    ← thin selector hook — granular reads from cartStore
      useCartDrawer.ts              ← drawer open/close (extends UIStore or local ref)
      index.ts
    types/
      index.ts                      ← CartUIItem (extends CartItem + display helpers)
    __tests__/
      useCart.test.ts

shared/
  components/
    Navbar.tsx                      ← +CartIcon with badge (MODIFY)
    ui/
      CartBadge.tsx                 ← reusable badge counter (new)

store/
  cartStore.ts                      ← audit + optional hardening (MODIFY if needed)
  types.ts                          ← align ingredientes_excluidos: number[] (MODIFY if needed)
```

---

## Component Design

### CartItemRow

```tsx
// Renders a single cart item row.
// Props: item: CartItem, onQuantityChange, onRemove
// Layout (mobile): stacked — image top, name+price middle, stepper+remove bottom
// Layout (desktop): horizontal — image left, content center, stepper+remove right
//
// ARIA:
//   - article role with aria-label="Producto: {name}"
//   - remove button: aria-label="Eliminar {name} del carrito"
//   - stepper: see QuantityStepper design
```

Key rendering decisions:
- Image: `loading="lazy"` with fallback SVG on `onError`
- Ingredient exclusions: displayed as `"Sin: {ingredient_name}"` pills using `text-muted-foreground` tokens
- Price: `Intl.NumberFormat` for currency formatting (ARS or USD depending on env)
- Uses `text-foreground`, `text-muted-foreground`, `bg-card`, `border-border` — zero raw colors

### QuantityStepper

```tsx
// Accessible +/- quantity input.
// Props: value, min (default 1), max (default 99), onChange, productName (for ARIA)
//
// ARIA:
//   - role="group" with aria-label="Cantidad de {productName}"
//   - decrement button: aria-label="Disminuir cantidad"
//   - increment button: aria-label="Aumentar cantidad"
//   - input: aria-label="Cantidad", type="number", min, max
//   - At min: decrement shows "Eliminar" behavior (quantity → 0 triggers remove)
//
// Behavior:
//   - Calls onChange with new value
//   - Does NOT call removeItem directly — parent (CartItemRow) decides behavior at 0
```

### OrderSummary

```tsx
// Right panel on desktop, bottom section on mobile.
// Shows: item count, subtotal, "Proceder al pago" CTA
//
// CTA behavior:
//   - Disabled when cart is empty
//   - When authenticated: navigates to /checkout (future change)
//   - When not authenticated: navigates to /login with state: { from: '/checkout' }
//
// Uses granular selectors:
//   const itemCount = useCartStore((s) => s.totalItems())
//   const total = useCartStore((s) => s.totalPrice())
```

### EmptyCart

```tsx
// Rendered when items.length === 0.
// Content: SVG illustration (inline, not image — avoids network request)
//          Heading: "Tu carrito está vacío"
//          Subtext: "Explorá nuestros productos y agregá lo que más te guste"
//          CTA: Link to /catalog — "Ver productos"
//
// Accessibility: heading h2, decorative SVG has aria-hidden="true"
```

### CartDrawer

```tsx
// Slide-in drawer from right side.
// Trigger: CartIcon in Navbar (via UIStore flag)
// Content: ScrollArea with CartItemRow list + OrderSummary footer
// 
// ARIA:
//   - role="dialog" aria-modal="true" aria-label="Carrito de compras"
//   - Trap focus when open (keyboard accessible)
//   - Escape closes drawer
//   - Backdrop click closes drawer
//
// Animation: CSS translate + transition (Tailwind v4 classes)
//   closed: translate-x-full
//   open:   translate-x-0
//
// Responsive: same component, full-screen on mobile (inset-0), 420px wide on desktop
```

### CartIcon (Navbar addition)

```tsx
// Added to Navbar right section, before theme toggle.
// Shows ShoppingCart icon from lucide-react.
// Badge: totalItems() value, hidden when 0.
//
// Granular selector:
//   const count = useCartStore((s) => s.totalItems())
//   // Only re-renders when item count changes, not when prices or names change
//
// ARIA:
//   - button aria-label="Carrito, {count} productos"
//   - badge: aria-live="polite" aria-atomic="true"
//
// Badge design: absolute positioned, top-right of icon, bg-destructive text-destructive-foreground
```

---

## State Management Design

### Selector Strategy (granular subscriptions)

```ts
// CORRECT — subscribe to derived primitive:
const count = useCartStore((s) => s.totalItems())
const total = useCartStore((s) => s.totalPrice())
const items = useCartStore((s) => s.items)

// CORRECT — single item selector:
const item = useCartStore((s) => s.getItem(productId))

// WRONG — full store subscription (causes all-renders):
const store = useCartStore()  // ← NEVER DO THIS
```

### useCart hook

```ts
// features/cart/hooks/useCart.ts
// Aggregates the most common cart reads for components.
// Does NOT wrap actions — components import actions directly to avoid re-render coupling.

export function useCart() {
  const items = useCartStore((s) => s.items)
  const totalItems = useCartStore((s) => s.totalItems())
  const totalPrice = useCartStore((s) => s.totalPrice())
  const isEmpty = items.length === 0

  return { items, totalItems, totalPrice, isEmpty }
}
```

### UIStore — CartDrawer state

Rather than adding a new flag to UIStore (which would require its tests to be updated), the CartDrawer will use a **local React state** in CartDrawer.tsx, with the trigger living in Navbar via a shared React context or a simple ref-based approach.

Decision: use a lightweight `useCartDrawer` hook backed by a Zustand store slice OR a simple React context. Given the project uses Zustand v5 for all UI state, the cleanest approach is to add `cartDrawerOpen` to UIStore:

```ts
// Addition to UIStore interface (store/types.ts):
cartDrawerOpen: boolean
toggleCartDrawer: () => void
setCartDrawerOpen: (open: boolean) => void
```

This keeps all UI state centralized and avoids prop drilling.

### CartStore — Type Audit

Current `CartItem.ingredientes_excluidos: string[]` — needs to be `number[]` to match:
- `RN-CR04`: "el cliente puede excluir ingredientes al agregar un producto"
- `RN-CR05`: "la personalización se guarda como array de IDs de ingredientes"
- Backend `DetallePedido.personalizacion`: `INTEGER[]`

**Action**: Update `types.ts` → `ingredientes_excluidos?: number[]`

### CartStore — updateQuantity behavior

Current implementation removes item when `quantity <= 0`. This is correct per spec:
- `updateQuantity('id', 0)` → removes item (consistent with "minimum effective quantity is 1")
- Explicit minimum validation in QuantityStepper: shows "remove" affordance at quantity=1

No changes needed to cartStore business logic.

---

## Tailwind v4 Design Tokens

All components use **only semantic tokens** from `@theme`. Zero raw color values.

### Food Store palette additions (if not already in app.css)

```css
@theme {
  /* Food store brand — warm amber/orange for appetite appeal */
  --color-brand: oklch(72% 0.18 55);          /* warm amber */
  --color-brand-foreground: oklch(15% 0.02 55);

  /* Cart badge / destructive accent */
  /* --color-destructive already defined in base theme */

  /* Success for "in stock", add-to-cart confirmation */
  /* --color-success already defined in existing ProductCard usage */

  /* Cart item row backgrounds */
  --color-cart-item-bg: oklch(98% 0.005 264);  /* slightly warm white */
  --color-cart-item-border: oklch(92% 0.01 264);
}
```

> Note: If `--color-success` and `--color-brand` already exist in `app.css`, do not redefine them.

### Typography hierarchy in CartPage

```
CartPage heading:    text-2xl font-bold text-foreground         (page title)
Item name:           text-base font-semibold text-foreground
Item price:          text-lg font-bold text-primary
Item personalization: text-xs text-muted-foreground
Subtotal label:      text-sm text-muted-foreground
Subtotal value:      text-xl font-bold text-foreground
CTA button:          text-base font-semibold
```

### Spacing rhythm

```
Page container:  px-4 sm:px-6 lg:px-8, max-w-screen-xl mx-auto
Cart list gap:   space-y-3
Item padding:    p-4
Drawer width:    w-full sm:w-[420px]
```

---

## Layout Architecture

### CartPage — Desktop (lg+)

```
┌────────────────────────────────────────────────────────────┐
│  [h1: Mi carrito]  [Vaciar carrito button]                  │
├──────────────────────────────────┬─────────────────────────┤
│  Cart Items List (scrollable)    │  Order Summary (sticky) │
│  ┌──────────────────────────┐    │  ─────────────────────  │
│  │ [img] Pepperoni Pizza    │    │  3 productos             │
│  │       $10.99  [- 2 +] 🗑 │    │  Subtotal: $35.00        │
│  │       Sin: cebolla       │    │                          │
│  └──────────────────────────┘    │  [Proceder al pago →]   │
│  ┌──────────────────────────┐    │                          │
│  │ [img] Calzone            │    │                          │
│  │       $12.99  [- 1 +] 🗑 │    │                          │
│  └──────────────────────────┘    │                          │
└──────────────────────────────────┴─────────────────────────┘
```

### CartPage — Mobile

```
┌──────────────────────┐
│ ← Mi carrito         │
│ ─────────────────── │
│ [img] Pizza Pepperoni│
│ $10.99               │
│ Sin: cebolla         │
│ [- 2 +]    🗑        │
│ ─────────────────── │
│ [img] Calzone        │
│ $12.99               │
│ [- 1 +]    🗑        │
│ ─────────────────── │
│ 3 productos          │
│ Subtotal: $35.00     │
│ [Proceder al pago →] │
│ [Vaciar carrito]     │
└──────────────────────┘
```

### CartDrawer

```
┌──────────────────────┐  ←  right edge of screen
│ Carrito      [✕]     │
│ ──────────────────── │
│ (scrollable list)    │
│ CartItemRow × N      │
│ ──────────────────── │
│ Subtotal: $35.00     │
│ [Ver carrito completo]│
│ [Proceder al pago →] │
└──────────────────────┘
```

---

## Responsive Strategy

Following mobile-first from `tailwind-design-system` skill:

| Breakpoint | CartPage Layout | CartDrawer |
|------------|-----------------|------------|
| mobile (< sm) | Single column, OrderSummary below list | Full-screen overlay |
| sm (640px+) | Single column, wider content | 420px right panel |
| lg (1024px+) | Two-column: 60% list / 40% summary | 420px right panel |

---

## Performance Patterns (vercel-react-best-practices)

1. **`bundle-dynamic-imports`**: CartPage is already lazy-loaded in Router.tsx. CartDrawer is loaded lazily from Navbar.
2. **`rerender-derived-state`**: `isEmpty` derived during render, not stored in state.
3. **`rerender-derived-state-no-effect`**: No `useEffect` for cart totals — computed via store selectors called inline.
4. **`client-localstorage-schema`**: Cart localStorage key is `food-store-cart` with `version: 0` — schema is versioned by Zustand persist.
5. **`rerender-simple-expression-in-memo`**: No unnecessary `useMemo` for simple derived values like `isEmpty`.
6. **`rerender-no-inline-components`**: CartItemRow is extracted, not defined inline.

---

## Accessibility Design (ui-design-system + WCAG 2.1 AA)

| Component | ARIA Pattern |
|-----------|--------------|
| CartPage | `<main>`, `<h1>`, landmark regions |
| CartItemRow | `<article>` with `aria-label` |
| QuantityStepper | `role="group"`, buttons with `aria-label`, input with `aria-label` |
| CartDrawer | `role="dialog"`, `aria-modal="true"`, focus trap, Escape key |
| CartIcon badge | `aria-label` on button with count, `aria-live="polite"` on badge |
| EmptyCart | Decorative SVG with `aria-hidden`, h2 heading |
| CTA buttons | `disabled` attribute when cart empty, `aria-disabled` for consistency |

**Color contrast**: All text/background token pairs must meet 4.5:1 minimum. Using OKLCH tokens ensures predictable perceptual contrast.

---

## E2E Test Design

File: `frontend/e2e/cart/cart-flows.spec.ts`

Test scenarios:
1. **Add item → badge updates**: Add product from catalog page → assert Navbar badge shows count
2. **Open CartPage**: Navigate to `/cart` → assert items rendered
3. **Quantity increment**: Click `+` on item → assert quantity updates in UI and localStorage
4. **Quantity decrement to 1**: Click `-` at quantity 2 → assert quantity becomes 1 (not removed)
5. **Remove item**: Click trash icon → assert item disappears from list
6. **Clear cart**: Click "Vaciar carrito" → assert empty state renders
7. **Persist across reload**: Add item → reload page → assert item still present
8. **Empty state**: Empty cart → assert empty state illustration and CTA visible
9. **Checkout CTA — unauthenticated**: Not logged in → click CTA → redirected to `/login`
10. **Checkout CTA — authenticated**: Logged in → click CTA → (placeholder for future checkout)

Auth seeding via `loginAs(page, 'CLIENT')` from `e2e/helpers/auth.ts` (existing pattern).

---

## File Creation Checklist

New files:
- `frontend/src/pages/CartPage.tsx`
- `frontend/src/features/cart/components/CartItemRow.tsx`
- `frontend/src/features/cart/components/QuantityStepper.tsx`
- `frontend/src/features/cart/components/OrderSummary.tsx`
- `frontend/src/features/cart/components/EmptyCart.tsx`
- `frontend/src/features/cart/components/index.ts`
- `frontend/src/features/cart/hooks/useCart.ts`
- `frontend/src/features/cart/hooks/index.ts`
- `frontend/src/features/cart/types/index.ts`
- `frontend/src/features/cart/__tests__/CartItemRow.test.tsx`
- `frontend/src/features/cart/__tests__/QuantityStepper.test.tsx`
- `frontend/src/features/cart/__tests__/OrderSummary.test.tsx`
- `frontend/src/features/cart/__tests__/useCart.test.ts`
- `frontend/src/widgets/CartDrawer/CartDrawer.tsx`
- `frontend/src/widgets/CartDrawer/index.ts`
- `frontend/src/widgets/CartDrawer/__tests__/CartDrawer.test.tsx`
- `frontend/e2e/cart/cart-flows.spec.ts`

Modified files:
- `frontend/src/shared/components/Navbar.tsx` — add CartIcon + badge
- `frontend/src/app/Router.tsx` — replace `/cart` Admin placeholder with CartPage
- `frontend/src/store/types.ts` — `ingredientes_excluidos?: number[]`
- `frontend/src/store/uiStore.ts` — add `cartDrawerOpen`, `toggleCartDrawer`, `setCartDrawerOpen`
- `frontend/src/app/App.css` or equivalent — verify food-store color tokens exist

Possibly modified:
- `frontend/src/store/cartStore.ts` — only if audit reveals issues (likely no changes needed)
