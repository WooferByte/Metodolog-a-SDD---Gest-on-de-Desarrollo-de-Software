# Manual Testing Guide: CHANGE 8 (frontend-zustand-stores-setup)

**Date**: 2026-05-07  
**Status**: Ready for Manual Verification  
**Automated Tests**: 70/70 passing ✅  
**Build**: npm run build passing ✅  

---

## Before You Start

- ✅ All 70 automated tests pass in 2.70s
- ✅ Build passes with no TypeScript errors
- ✅ 4 stores created with proper TypeScript types
- ✅ localStorage persistence configured correctly
- ✅ Code committed: `5612da4 feat: implement 4 Zustand stores (auth, cart, payment, ui)`

**This guide walks you through manual verification of real-world behavior.**

---

## Test Matrix

| Category | Test # | Test Name | Expected Result | Status |
|----------|--------|-----------|-----------------|--------|
| **SETUP** | 1 | Zustand installed | `npm list zustand` shows 5.0.8+ | |
| | 2 | Directory structure | `/store` folder exists with all 4 stores | |
| | 3 | TypeScript strict mode | No TS errors in `npm run test` | |
| **AUTH** | 4 | Login flow | Token stored and user authenticated | |
| | 5 | Logout flow | Tokens cleared, isAuthenticated = false | |
| | 6 | Role checking | hasRole('admin') returns correct boolean | |
| | 7 | localStorage persistence | Page reload keeps accessToken, loses refreshToken | |
| | 8 | SSR hydration safety | _hasHydrated flag prevents mismatch | |
| **CART** | 9 | Add item | Item appears in cart with quantity 1 | |
| | 10 | Increment item | Quantity increments when adding same product | |
| | 11 | Remove item | Item deleted from cart | |
| | 12 | Update quantity | Quantity reflects in totalItems and totalPrice | |
| | 13 | Computed totals | totalItems() and totalPrice() calculated correctly | |
| | 14 | Ingredient personalization | ingredientes_excluidos array maintained | |
| | 15 | localStorage persistence | Close tab, reopen → cart restored exactly | |
| | 16 | Multi-tab sync | Change cart in Tab A → Tab B updates automatically | |
| **PAYMENT** | 17 | Start checkout | checkoutStep = 'cart' | |
| | 18 | Progress workflow | Step sequence: cart → shipping → payment → confirmation | |
| | 19 | Set preference | preferenceId stored in state | |
| | 20 | Payment status | updatePaymentStatus tracks 'pending','success','failed' | |
| | 21 | Reset payment | resetPayment() clears all state | |
| | 22 | NO persistence | Page reload during checkout → state empty | |
| **UI** | 23 | Set theme | theme state updates (light/dark) | |
| | 24 | Sidebar toggle | sidebarOpen state toggles | |
| | 25 | Add toast | Toast appears in toasts array with ID | |
| | 26 | Remove toast | Toast removed from array | |
| | 27 | Theme persistence | Close tab → theme remembered | |
| | 28 | Sidebar NOT persisted | Close tab → sidebar resets to default | |
| | 29 | Toasts NOT persisted | Page reload → toasts disappear | |

---

## Section 1: Setup Verification (5 minutes)

### Test 1: Zustand Installed
```bash
npm list zustand
# Expected: zustand@5.0.8 or newer
# ✅ PASS if version >= 5.0.8
```

### Test 2: Directory Structure
```bash
ls -la frontend/src/store/
# Expected output:
# - authStore.ts
# - cartStore.ts
# - paymentStore.ts
# - uiStore.ts
# - types.ts
# - index.ts
# - examples/ (with 3 example components)
# - __tests__/ (with 4 test files)
```

### Test 3: TypeScript Strict Mode
```bash
cd frontend && npm run test
# Look for: "Test Files 4 passed (4)" and "Tests 70 passed (70)"
# ✅ PASS if all 70 tests pass with 0 failures
```

---

## Section 2: AuthStore Testing (10 minutes)

### Setup: Start Dev Server
```bash
cd frontend
npm run dev
# Note the URL (usually http://localhost:5173)
```

### Test 4: Login Flow

1. Open browser DevTools → Console
2. Run this code:
```javascript
// Import the auth store
import { useAuthStore } from './src/store'

// Simulate login
const store = useAuthStore.getState()
store.updateTokens('test-access-token-123', 'test-refresh-token-456')
store.setUser({
  id: 'user-1',
  email: 'test@example.com',
  name: 'Test User',
  roles: ['customer']
})

// Verify
console.log('isAuthenticated:', store.isAuthenticated) // Should be true
console.log('user:', store.user) // Should show user data
console.log('accessToken:', store.accessToken) // Should be 'test-access-token-123'
console.log('refreshToken:', store.refreshToken) // Should be 'test-refresh-token-456'
```

✅ **PASS**: All values logged correctly, isAuthenticated = true

### Test 5: Logout Flow
```javascript
const store = useAuthStore.getState()
store.logout()

// Verify
console.log('isAuthenticated:', store.isAuthenticated) // Should be false
console.log('accessToken:', store.accessToken) // Should be null
console.log('refreshToken:', store.refreshToken) // Should be null
console.log('user:', store.user) // Should be null
```

✅ **PASS**: All cleared, isAuthenticated = false

### Test 6: Role Checking
```javascript
const store = useAuthStore.getState()
store.setUser({
  id: 'user-1',
  email: 'admin@example.com',
  name: 'Admin User',
  roles: ['admin', 'customer']
})

console.log('Has admin role:', store.hasRole('admin')) // Should be true
console.log('Has customer role:', store.hasRole('customer')) // Should be true
console.log('Has superuser role:', store.hasRole('superuser')) // Should be false
```

✅ **PASS**: Role checking works correctly

### Test 7: localStorage Persistence
```javascript
// After login (Test 4), check localStorage
console.log('localStorage:', localStorage.getItem('food-store-auth'))
// Should show: {"accessToken":"test-access-token-123"}
// NOTE: refreshToken should NOT be there

// Now refresh the page
location.reload()

// After page reload, check if accessToken is restored
import { useAuthStore } from './src/store'
const store = useAuthStore.getState()
console.log('After reload - accessToken:', store.accessToken) // Should be 'test-access-token-123'
console.log('After reload - refreshToken:', store.refreshToken) // Should be null (not persisted)
```

✅ **PASS**: accessToken restored, refreshToken NOT restored

### Test 8: SSR Hydration Safety
```javascript
import { useAuthStore } from './src/store'
const store = useAuthStore.getState()
console.log('_hasHydrated:', store._hasHydrated) // Should be true after hydration
```

✅ **PASS**: _hasHydrated flag is true

---

## Section 3: CartStore Testing (15 minutes)

### Test 9: Add Item to Cart
```javascript
import { useCartStore } from './src/store'
const store = useCartStore.getState()

store.addItem({
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 12.99,
  quantity: 1
})

console.log('Cart items:', store.items)
// Expected: [{ productId: 'pizza-001', name: 'Pepperoni Pizza', price: 12.99, quantity: 1 }]
```

✅ **PASS**: Item added to cart

### Test 10: Increment Item (Add Duplicate)
```javascript
const store = useCartStore.getState()

// Add same pizza again
store.addItem({
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 12.99,
  quantity: 1
})

console.log('Cart items:', store.items)
// Expected: [{ productId: 'pizza-001', ..., quantity: 2 }]
// Quantity should increment, not duplicate item
```

✅ **PASS**: Quantity incremented, not duplicated

### Test 11: Remove Item
```javascript
const store = useCartStore.getState()

// First add items
store.clearCart() // Start fresh
store.addItem({
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 12.99,
  quantity: 1
})
store.addItem({
  productId: 'burger-001',
  name: 'Cheese Burger',
  price: 8.99,
  quantity: 1
})

// Remove pizza
store.removeItem('pizza-001')

console.log('Cart items:', store.items)
// Expected: [{ productId: 'burger-001', name: 'Cheese Burger', ... }]
```

✅ **PASS**: Item removed, burger remains

### Test 12: Update Quantity
```javascript
const store = useCartStore.getState()

// Start with burger
store.clearCart()
store.addItem({
  productId: 'burger-001',
  name: 'Cheese Burger',
  price: 8.99,
  quantity: 1
})

// Update quantity to 3
store.updateQuantity('burger-001', 3)

console.log('Cart items:', store.items)
// Expected: [{ productId: 'burger-001', ..., quantity: 3 }]
```

✅ **PASS**: Quantity updated to 3

### Test 13: Computed Totals
```javascript
const store = useCartStore.getState()

// Clear and add multiple items
store.clearCart()
store.addItem({
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 12.99,
  quantity: 2  // 2x $12.99 = $25.98
})
store.addItem({
  productId: 'burger-001',
  name: 'Cheese Burger',
  price: 8.99,
  quantity: 3  // 3x $8.99 = $26.97
})

console.log('Total Items:', store.totalItems()) // Expected: 5
console.log('Total Price:', store.totalPrice()) // Expected: 52.95 (25.98 + 26.97)
```

✅ **PASS**: totalItems() = 5, totalPrice() ≈ 52.95

### Test 14: Ingredient Personalization
```javascript
const store = useCartStore.getState()

store.clearCart()
store.addItem({
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 12.99,
  quantity: 1,
  ingredientes_excluidos: ['onion', 'garlic']  // No onion or garlic
})

const item = store.getItem('pizza-001')
console.log('Item:', item)
// Expected: { ..., ingredientes_excluidos: ['onion', 'garlic'] }
```

✅ **PASS**: Ingredient exclusions maintained

### Test 15: localStorage Persistence
```javascript
const store = useCartStore.getState()

// Verify localStorage has cart data
console.log('localStorage food-store-cart:', localStorage.getItem('food-store-cart'))
// Should contain: { "items": [...] }

// Refresh page
location.reload()

// After reload, cart should be restored
import { useCartStore } from './src/store'
const newStore = useCartStore.getState()
console.log('After reload - Cart items:', newStore.items)
// Expected: Same items as before reload
```

✅ **PASS**: Cart restored after page reload

### Test 16: Multi-Tab Synchronization

1. Open the same app in **two browser tabs**
2. In **Tab A** console:
```javascript
import { useCartStore } from './src/store'
const store = useCartStore.getState()
store.addItem({
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 12.99,
  quantity: 1
})
```

3. In **Tab B** console (without reload):
```javascript
import { useCartStore } from './src/store'
const store = useCartStore.getState()
console.log('Items:', store.items)
// Expected: Pizza from Tab A should appear automatically!
```

✅ **PASS**: Tab B automatically shows pizza added in Tab A

---

## Section 4: PaymentStore Testing (10 minutes)

### Test 17: Start Checkout
```javascript
import { usePaymentStore } from './src/store'
const store = usePaymentStore.getState()

store.startCheckout()

console.log('Checkout step:', store.checkoutStep) // Expected: 'cart'
console.log('Payment status:', store.paymentStatus) // Expected: 'pending'
```

✅ **PASS**: Checkout initialized

### Test 18: Workflow Progression
```javascript
const store = usePaymentStore.getState()

// Progress through steps
console.log('Step 1:', store.checkoutStep) // cart
store.updatePaymentStatus('pending')

// Simulate next steps
console.log('Step 2: shipping (simulated)')
console.log('Step 3: payment (simulated)')
console.log('Step 4: confirmation (simulated)')

// Final status
store.updatePaymentStatus('success')
console.log('Final status:', store.paymentStatus) // success
```

✅ **PASS**: Workflow progresses correctly

### Test 19: Set Preference ID
```javascript
const store = usePaymentStore.getState()

store.setPreference('pref-123-456')

console.log('Preference ID:', store.preferenceId) // Expected: 'pref-123-456'
```

✅ **PASS**: Preference ID stored

### Test 20: Payment Status Updates
```javascript
const store = usePaymentStore.getState()

store.updatePaymentStatus('pending')
console.log('Status:', store.paymentStatus) // pending

store.updatePaymentStatus('success')
console.log('Status:', store.paymentStatus) // success

store.updatePaymentStatus('failed')
console.log('Status:', store.paymentStatus) // failed
```

✅ **PASS**: Status updates correctly

### Test 21: Reset Payment
```javascript
const store = usePaymentStore.getState()

// Add data
store.startCheckout()
store.setPreference('pref-123-456')
store.updatePaymentStatus('success')

console.log('Before reset:', {
  step: store.checkoutStep,
  prefId: store.preferenceId,
  status: store.paymentStatus
})

// Reset
store.resetPayment()

console.log('After reset:', {
  step: store.checkoutStep, // Expected: null
  prefId: store.preferenceId, // Expected: null
  status: store.paymentStatus // Expected: null
})
```

✅ **PASS**: All payment state cleared

### Test 22: NO Persistence (Security Check)
```javascript
// Check localStorage - payment store should NOT be there
console.log('localStorage keys:', Object.keys(localStorage))
// Expected: ['food-store-auth', 'food-store-cart', 'food-store-ui']
// Should NOT have 'food-store-payment'

// Verify by checking config
const store = usePaymentStore.getState()
console.log('Is persisted:', store.persist) // Should be undefined (no middleware)

// Refresh page and verify state is empty
location.reload()

import { usePaymentStore } from './src/store'
const newStore = usePaymentStore.getState()
console.log('After reload - checkoutStep:', newStore.checkoutStep) // Expected: null
```

✅ **PASS**: Payment state NOT persisted, empty after reload

---

## Section 5: UIStore Testing (10 minutes)

### Test 23: Set Theme
```javascript
import { useUIStore } from './src/store'
const store = useUIStore.getState()

store.setTheme('dark')
console.log('Theme:', store.theme) // Expected: 'dark'

store.setTheme('light')
console.log('Theme:', store.theme) // Expected: 'light'
```

✅ **PASS**: Theme updates correctly

### Test 24: Sidebar Toggle
```javascript
const store = useUIStore.getState()

console.log('Sidebar open:', store.sidebarOpen) // Initial state
store.toggleSidebar()
console.log('Sidebar open:', store.sidebarOpen) // Toggled

store.toggleSidebar()
console.log('Sidebar open:', store.sidebarOpen) // Toggled back
```

✅ **PASS**: Sidebar toggles correctly

### Test 25: Add Toast
```javascript
const store = useUIStore.getState()

store.addToast({
  id: 'toast-1',
  message: 'Item added to cart',
  type: 'success'
})

console.log('Toasts:', store.toasts)
// Expected: [{ id: 'toast-1', message: 'Item added to cart', type: 'success' }]
```

✅ **PASS**: Toast added

### Test 26: Remove Toast
```javascript
const store = useUIStore.getState()

store.removeToast('toast-1')

console.log('Toasts:', store.toasts)
// Expected: [] (empty)
```

✅ **PASS**: Toast removed

### Test 27: Theme Persistence
```javascript
const store = useUIStore.getState()

// Set theme
store.setTheme('dark')

// Check localStorage
console.log('localStorage food-store-ui:', localStorage.getItem('food-store-ui'))
// Expected: { "theme": "dark" }

// Refresh
location.reload()

// After reload
import { useUIStore } from './src/store'
const newStore = useUIStore.getState()
console.log('Theme after reload:', newStore.theme) // Expected: 'dark'
```

✅ **PASS**: Theme persisted and restored

### Test 28: Sidebar NOT Persisted
```javascript
const store = useUIStore.getState()

// Check localStorage - should only have theme
console.log('localStorage food-store-ui:', localStorage.getItem('food-store-ui'))
// Expected: { "theme": "dark" } (NO sidebarOpen)

// Refresh
location.reload()

// After reload, sidebar should be default (not persisted)
import { useUIStore } from './src/store'
const newStore = useUIStore.getState()
console.log('Sidebar after reload:', newStore.sidebarOpen)
// Expected: initial default value (not what it was before reload)
```

✅ **PASS**: Sidebar not persisted

### Test 29: Toasts NOT Persisted
```javascript
const store = useUIStore.getState()

store.addToast({
  id: 'toast-2',
  message: 'Notification',
  type: 'info'
})

// Refresh page
location.reload()

// After reload, toasts should be gone
import { useUIStore } from './src/store'
const newStore = useUIStore.getState()
console.log('Toasts after reload:', newStore.toasts)
// Expected: [] (empty - not persisted)
```

✅ **PASS**: Toasts not persisted

---

## Final Verification Checklist

Before signing off, verify:

- [ ] Section 1 (Setup): 3/3 tests passed
- [ ] Section 2 (AuthStore): 5/5 tests passed (Tests 4-8)
- [ ] Section 3 (CartStore): 8/8 tests passed (Tests 9-16)
- [ ] Section 4 (PaymentStore): 6/6 tests passed (Tests 17-22)
- [ ] Section 5 (UIStore): 7/7 tests passed (Tests 23-29)

**Total Manual Tests**: 29/29 ✅

---

## Rollback (if needed)

If any manual test fails:

```bash
# Revert to previous commit
git revert HEAD

# Or go back to checkpoint
git reset --hard 6171522

# Restart CHANGE 8
openspec list --json
```

---

## Success Criteria

✅ **PASS**: All 29 manual tests pass + all 70 automated tests pass + build succeeds

**Ready to archive CHANGE 8** once manual verification complete.

---

**Last Updated**: 2026-05-07 08:45  
**Tested By**: [Your Name]  
**Date Tested**: [Today's Date]  
**Verdict**: ☐ PASS ☐ FAIL
