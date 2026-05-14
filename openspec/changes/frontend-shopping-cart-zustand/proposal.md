# Proposal: frontend-shopping-cart-zustand

## Summary

Implement the shopping cart feature as a complete, production-ready UI for the Food Store. This change covers the full cart experience: a `CartPage` with a drawer/slide-in panel variant, a persistent `CartDrawer` component accessible from any page, and a `CartIcon` badge in the Navbar that reflects real-time item count. The cart is 100% client-side — state is owned by `useCartStore` (Zustand v5 + devtools + persist), with no backend dependency for this change.

## Problem

The `/cart` route currently renders the placeholder `<Admin />` component. The `cartStore` exists with correct business logic but has no UI layer consuming it. Users cannot see, modify, or manage their cart — making it impossible to proceed to checkout. The Navbar has no cart indicator, so users have no feedback when adding items from the catalog.

## Solution

1. **CartPage** (`/cart`) — full-screen cart experience accessible from sidebar/navigation:
   - List of cart items with product image, name, price, quantity stepper, personalization summary, and remove action
   - Order summary panel: subtotal, item count, "Proceed to Checkout" CTA (disabled if empty, links to future checkout change)
   - Empty state with illustration and "Browse Products" CTA
   - All interactions wired to `useCartStore` actions (`addItem`, `removeItem`, `updateQuantity`, `clearCart`)

2. **CartDrawer** — slide-in panel from the right, accessible from any page via a floating trigger or Navbar icon:
   - Mirrors CartPage content but in compact drawer form
   - Opens/closes via a `cartDrawerOpen` flag in `useUIStore` (or inline local state via a shared context)
   - "View Full Cart" link navigates to `/cart`

3. **CartIcon (Navbar badge)** — real-time counter badge on a shopping cart icon in the Navbar, using a granular selector from `useCartStore` to avoid re-renders.

4. **Store audit & hardening** — verify `cartStore.ts` has correct `devtools(persist(...))` middleware order, `ingredientes_excluidos` typed as `number[]` (integer IDs per RN-CR04/05 and backend convention), `updateQuantity` enforces minimum 1 (auto-remove at 0), and all selectors are granular.

5. **Unit tests** (vitest) — complete suite for new components and hooks under `__tests__/`.

6. **E2E tests** (Playwright) — flows: add item → verify badge updates → open cart → change quantity → remove item → clear cart → empty state.

## Scope

**In scope:**
- `frontend/src/pages/CartPage.tsx`
- `frontend/src/features/cart/` — new feature directory with components, hooks, types
- `frontend/src/widgets/CartDrawer/` — drawer widget (creates the `widgets/` layer)
- `frontend/src/shared/components/Navbar.tsx` — add CartIcon with badge
- `frontend/src/app/Router.tsx` — replace `/cart` placeholder with `CartPage`
- `frontend/src/store/cartStore.ts` — audit and minor hardening if needed
- `frontend/src/store/types.ts` — update `ingredientes_excluidos` type if needed
- `frontend/e2e/cart/` — E2E specs
- `frontend/src/features/cart/__tests__/` — vitest unit tests

**Out of scope:**
- Backend checkout/order creation (next change: `frontend-checkout-payment`)
- MercadoPago SDK integration
- Address selection at checkout (handled by separate checkout change)
- Admin order management

## Acceptance Criteria

- [ ] `/cart` renders `CartPage` (not the Admin placeholder)
- [ ] Adding a product from catalog increments the Navbar badge immediately
- [ ] `addItem` with existing `productId` increments quantity — no duplicate rows
- [ ] `updateQuantity` enforces minimum 1; setting to 0 removes the item
- [ ] `clearCart` empties the cart and shows empty state
- [ ] `ingredientes_excluidos` per item displayed as human-readable ingredient names (or IDs as fallback)
- [ ] Cart persists across page reload (localStorage key `food-store-cart`)
- [ ] All interactive elements have correct ARIA labels
- [ ] Mobile layout is fully functional (stacked layout, full-width stepper)
- [ ] Desktop layout shows side-by-side items + order summary panel
- [ ] Zero raw color values — only semantic tokens from `@theme`
- [ ] React.lazy + Suspense applied to CartPage
- [ ] Zustand selectors are granular (no full store subscription)
- [ ] vitest coverage ≥ 40% for cart feature files
- [ ] E2E Playwright tests pass for all cart flows

## Dependencies

- **Predecessor**: `frontend-addresses-ui` (archived, git: ca0770f)
- **Successor**: `frontend-shopping-cart-ui` — visual polish pass, then `frontend-checkout-payment`
- **Runtime**: `useCartStore` (exists), `useUIStore` (exists for drawer state), `useAuthStore` (for route guard on checkout CTA)
- **No new packages required**: zustand, lucide-react, tailwind v4 all installed

## Risks

- `ingredientes_excluidos` currently typed as `string[]` in `types.ts` but backend uses `INTEGER[]`; may need to align with `number[]` during this change
- `CartDrawer` introduces the first widget in `widgets/` — FSD layer must be correctly initialized
- Navbar modification is a shared-component change — must not break existing auth/theme/sidebar behavior
