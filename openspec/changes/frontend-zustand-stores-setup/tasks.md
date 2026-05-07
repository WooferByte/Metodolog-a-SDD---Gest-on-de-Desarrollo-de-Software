## 1. Setup and Dependencies

- [ ] 1.1 Install Zustand v5.0.8 to frontend via npm
- [ ] 1.2 Create `frontend/src/store/` directory structure
- [ ] 1.3 Verify TypeScript strict mode is enabled in frontend tsconfig.json

## 2. AuthStore Implementation

- [ ] 2.1 Create `frontend/src/store/authStore.ts` with TypeScript interfaces
- [ ] 2.2 Implement authStore with authStore state (accessToken, refreshToken, user, isAuthenticated)
- [ ] 2.3 Implement authStore.updateTokens() action
- [ ] 2.4 Implement authStore.logout() action
- [ ] 2.5 Implement authStore.hasRole(role) helper method
- [ ] 2.6 Implement localStorage persistence for accessToken only using persist middleware
- [ ] 2.7 Add hydration safety with `_hasHydrated` flag to prevent SSR mismatch

## 3. CartStore Implementation

- [ ] 3.1 Create `frontend/src/store/cartStore.ts` with TypeScript types (CartItem, CartStore)
- [ ] 3.2 Implement cartStore.items state as array of cart items
- [ ] 3.3 Implement cartStore.addItem() - add or increment if already exists
- [ ] 3.4 Implement cartStore.removeItem(productId) action
- [ ] 3.5 Implement cartStore.updateQuantity(productId, cantidad) action
- [ ] 3.6 Implement cartStore.clearCart() action
- [ ] 3.7 Implement computed selectors: totalItems() and totalPrice()
- [ ] 3.8 Implement getItem(productId) selector
- [ ] 3.9 Implement localStorage persistence with key "food-store-cart" using persist middleware
- [ ] 3.10 Support ingredient personalization (ingredientes_excluidos array)

## 4. PaymentStore Implementation

- [ ] 4.1 Create `frontend/src/store/paymentStore.ts` with TypeScript types
- [ ] 4.2 Implement paymentStore state: checkoutStep, preferenceId, paymentStatus
- [ ] 4.3 Implement paymentStore.startCheckout() - initialize workflow
- [ ] 4.4 Implement paymentStore.setPreference(preferenceId) action
- [ ] 4.5 Implement paymentStore.updatePaymentStatus(status) action
- [ ] 4.6 Implement paymentStore.resetPayment() to clear state
- [ ] 4.7 Verify NO localStorage persistence (explicit: pass empty storage config)

## 5. UIStore Implementation

- [ ] 5.1 Create `frontend/src/store/uiStore.ts` with TypeScript types
- [ ] 5.2 Implement uiStore.theme state (light/dark)
- [ ] 5.3 Implement uiStore.setTheme(theme) action
- [ ] 5.4 Implement uiStore.sidebarOpen state
- [ ] 5.5 Implement uiStore.toggleSidebar() action
- [ ] 5.6 Implement uiStore.toasts state as array
- [ ] 5.7 Implement uiStore.addToast(toast) action
- [ ] 5.8 Implement uiStore.removeToast(toastId) action
- [ ] 5.9 Implement localStorage persistence for theme ONLY using partialize middleware
- [ ] 5.10 Verify sidebar and toasts do NOT persist

## 6. Store Exports and Type Definitions

- [ ] 6.1 Create `frontend/src/store/index.ts` that re-exports all store hooks
- [ ] 6.2 Create `frontend/src/store/types.ts` with all TypeScript interfaces (AuthStore, CartStore, etc.)
- [ ] 6.3 Add JSDoc comments to each store explaining usage
- [ ] 6.4 Export type definitions for use in components

## 7. Testing

- [ ] 7.1 Create `frontend/src/store/__tests__/authStore.test.ts` with tests for login/logout/roles
- [ ] 7.2 Create `frontend/src/store/__tests__/cartStore.test.ts` with tests for add/remove/totals
- [ ] 7.3 Create `frontend/src/store/__tests__/paymentStore.test.ts` with tests for checkout steps
- [ ] 7.4 Create `frontend/src/store/__tests__/uiStore.test.ts` with tests for theme/sidebar/toasts
- [ ] 7.5 Test authStore localStorage persistence of accessToken
- [ ] 7.6 Test cartStore localStorage persistence
- [ ] 7.7 Test paymentStore has NO persistence (loads empty on page reload)
- [ ] 7.8 Test multi-tab synchronization for localStorage-persisted stores
- [ ] 7.9 Verify all tests pass and have >60% coverage

## 8. Integration and Documentation

- [ ] 8.1 Create example component using authStore to demonstrate selector pattern
- [ ] 8.2 Create example component using cartStore
- [ ] 8.3 Create example component using paymentStore
- [ ] 8.4 Create `STORE_USAGE.md` documenting how to use each store
- [ ] 8.5 Add Zustand dependency version to `frontend/package.json` with note about TypeScript requirements
- [ ] 8.6 Verify build passes with `npm run build`
- [ ] 8.7 Commit with message: "feat: implement 4 Zustand stores (auth, cart, payment, ui)"

