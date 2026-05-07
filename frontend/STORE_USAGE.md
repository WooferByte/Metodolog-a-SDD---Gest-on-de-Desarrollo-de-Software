# Store Usage Guide

This document explains how to use each Zustand store in the Food Store frontend application.

## Overview

The frontend uses four separate Zustand stores for different concerns:

| Store | Purpose | Persists | Use Case |
|-------|---------|----------|----------|
| **authStore** | JWT tokens, user data, roles | accessToken only | Authentication, authorization |
| **cartStore** | Shopping cart items | All items & quantities | Shopping cart management |
| **paymentStore** | Checkout workflow | None (security) | Payment process, multi-step checkout |
| **uiStore** | Theme, sidebar, toasts | Theme only | UI preferences, notifications |

## 1. AuthStore - Authentication Management

### Purpose
Manages JWT tokens, user authentication state, and role-based access control.

### State
```typescript
{
  accessToken: string | null        // JWT access token (persisted)
  refreshToken: string | null       // JWT refresh token (NOT persisted)
  user: {                           // User data
    id: string
    email: string
    name: string
    roles: string[]
  } | null
  isAuthenticated: boolean          // Computed from accessToken
  _hasHydrated: boolean             // SSR hydration flag
}
```

### Key Actions

#### updateTokens(accessToken, refreshToken)
Updates JWT tokens after successful login.
```typescript
const updateTokens = useAuthStore((state) => state.updateTokens)
updateTokens('jwt-access-token', 'jwt-refresh-token')
```

#### setUser(user)
Stores authenticated user data.
```typescript
const setUser = useAuthStore((state) => state.setUser)
setUser({
  id: '123',
  email: 'user@example.com',
  name: 'John Doe',
  roles: ['customer']
})
```

#### logout()
Clears all authentication state.
```typescript
const logout = useAuthStore((state) => state.logout)
logout()
```

#### hasRole(role)
Helper to check if user has specific role.
```typescript
const hasRole = useAuthStore((state) => state.hasRole)
if (hasRole('admin')) {
  // Show admin features
}
```

### Usage in Components
```tsx
import { useAuthStore } from '@/store'

function UserProfile() {
  // Selector pattern - only re-renders when selected state changes
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  
  if (!isAuthenticated) return <div>Please login</div>
  
  return (
    <div>
      <h2>{user?.name}</h2>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

### Persistence
- **What persists**: `accessToken` only
- **Storage**: localStorage with key `food-store-auth`
- **Why**: Access token can be re-generated, but refresh token should never be in localStorage
- **Survive**: Logout, page reload, app restart

### SSR Safety
The store includes `_hasHydrated` flag to prevent hydration mismatches in Next.js:
```tsx
function App() {
  const hasHydrated = useAuthStore((state) => state._hasHydrated)
  
  if (!hasHydrated) return null // Wait for hydration
  
  return <MainApp />
}
```

---

## 2. CartStore - Shopping Cart Management

### Purpose
Manages shopping cart items, quantities, and calculated totals with support for ingredient personalization.

### State
```typescript
{
  items: CartItem[]  // Array of items in cart
}

type CartItem = {
  productId: string
  name: string
  price: number
  quantity: number
  image?: string
  ingredientes_excluidos?: string[]  // Ingredient customization
}
```

### Key Actions

#### addItem(item)
Adds item to cart or increments quantity if already exists.
```typescript
const addItem = useCartStore((state) => state.addItem)
addItem({
  productId: 'pizza-001',
  name: 'Pepperoni Pizza',
  price: 12.99,
  quantity: 1,
  ingredientes_excluidos: ['onion']
})
```

#### removeItem(productId)
Removes item from cart.
```typescript
const removeItem = useCartStore((state) => state.removeItem)
removeItem('pizza-001')
```

#### updateQuantity(productId, quantity)
Updates quantity (removes if <= 0).
```typescript
const updateQuantity = useCartStore((state) => state.updateQuantity)
updateQuantity('pizza-001', 5)
updateQuantity('pizza-001', 0)  // Removes item
```

#### clearCart()
Empties the entire cart.
```typescript
const clearCart = useCartStore((state) => state.clearCart)
clearCart()
```

#### getItem(productId)
Finds specific item in cart.
```typescript
const getItem = useCartStore((state) => state.getItem)
const item = getItem('pizza-001')
```

### Computed Selectors

#### totalItems()
Sum of all item quantities.
```typescript
const totalItems = useCartStore((state) => state.totalItems)
console.log(totalItems())  // e.g., 5
```

#### totalPrice()
Sum of (price * quantity) for all items.
```typescript
const totalPrice = useCartStore((state) => state.totalPrice)
console.log(totalPrice().toFixed(2))  // e.g., "49.95"
```

### Usage in Components
```tsx
import { useCartStore } from '@/store'

function CartSummary() {
  const totalItems = useCartStore((state) => state.totalItems)
  const totalPrice = useCartStore((state) => state.totalPrice)
  
  return (
    <div>
      <span>{totalItems()} items | ${totalPrice().toFixed(2)}</span>
    </div>
  )
}

function CartItems() {
  const items = useCartStore((state) => state.items)
  const updateQuantity = useCartStore((state) => state.updateQuantity)
  const removeItem = useCartStore((state) => state.removeItem)
  
  return (
    <ul>
      {items.map((item) => (
        <li key={item.productId}>
          <h3>{item.name}</h3>
          <p>${item.price}</p>
          <input
            type="number"
            value={item.quantity}
            onChange={(e) => updateQuantity(item.productId, parseInt(e.target.value))}
          />
          <button onClick={() => removeItem(item.productId)}>Remove</button>
        </li>
      ))}
    </ul>
  )
}
```

### Persistence
- **What persists**: All items with quantities and personalization
- **Storage**: localStorage with key `food-store-cart`
- **Survive**: Page reload, tab close, logout/login
- **Note**: Cart persists even after logout (acceptable UX - users expect this)

### Multi-Tab Synchronization
Cart automatically syncs across tabs:
- User adds item in Tab A
- Tab B automatically updates cart
- Powered by Zustand persist middleware listening to localStorage events

---

## 3. PaymentStore - Checkout Workflow

### Purpose
Manages multi-step checkout process and payment status with MercadoPago integration.

### State
```typescript
{
  checkoutStep: 'cart' | 'shipping' | 'payment' | 'confirmation'
  preferenceId: string | null       // MercadoPago preference ID
  paymentStatus: 'idle' | 'processing' | 'completed' | 'failed'
}
```

### Key Actions

#### startCheckout()
Initializes checkout workflow from cart screen.
```typescript
const startCheckout = usePaymentStore((state) => state.startCheckout)
startCheckout()  // Changes step to 'shipping'
```

#### setPreference(preferenceId)
Stores MercadoPago preference ID and moves to payment step.
```typescript
const setPreference = usePaymentStore((state) => state.setPreference)
// After calling MercadoPago API
setPreference('mp-pref-123456')  // Changes step to 'payment'
```

#### updatePaymentStatus(status)
Updates payment status during processing.
```typescript
const updatePaymentStatus = usePaymentStore((state) => state.updatePaymentStatus)
updatePaymentStatus('processing')
updatePaymentStatus('completed')
updatePaymentStatus('failed')
```

#### resetPayment()
Resets payment state to initial (for retries or new purchase).
```typescript
const resetPayment = usePaymentStore((state) => state.resetPayment)
resetPayment()  // Back to step: 'cart'
```

### Usage in Components
```tsx
import { usePaymentStore } from '@/store'

function CheckoutWizard() {
  const checkoutStep = usePaymentStore((state) => state.checkoutStep)
  const paymentStatus = usePaymentStore((state) => state.paymentStatus)
  const startCheckout = usePaymentStore((state) => state.startCheckout)
  const setPreference = usePaymentStore((state) => state.setPreference)
  const updatePaymentStatus = usePaymentStore((state) => state.updatePaymentStatus)
  
  const handleCreatePayment = async () => {
    updatePaymentStatus('processing')
    try {
      const response = await createMercadoPagoPreference()
      setPreference(response.id)  // Moves to payment step
      updatePaymentStatus('idle')
    } catch (error) {
      updatePaymentStatus('failed')
    }
  }
  
  return (
    <div>
      {checkoutStep === 'cart' && (
        <button onClick={startCheckout}>Proceed to Checkout</button>
      )}
      {checkoutStep === 'payment' && (
        <button onClick={handleCreatePayment}>Create Payment</button>
      )}
      {paymentStatus === 'completed' && (
        <p>Payment successful!</p>
      )}
    </div>
  )
}
```

### Persistence
- **What persists**: NOTHING (zero persistence)
- **Why**: Security - payment state must never survive page reload
- **UX Trade-off**: If user refreshes mid-checkout, they restart from step 1
- **Acceptable**: Security > convenience for payment

### Important Notes
- **No localStorage storage** - Payment store does NOT use persist middleware
- **State clears on reload** - Essential for payment security
- **Prevent payment hijacking** - Ensures stale checkout sessions can't be resumed

---

## 4. UIStore - UI Preferences and Notifications

### Purpose
Manages theme preferences, sidebar visibility, and toast notifications.

### State
```typescript
{
  theme: 'light' | 'dark'           // Theme preference (persisted)
  sidebarOpen: boolean              // Sidebar state (ephemeral)
  toasts: Toast[]                   // Notification queue (ephemeral)
  _hasHydrated: boolean             // SSR hydration flag
}

type Toast = {
  id: string
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration?: number
}
```

### Key Actions

#### setTheme(theme)
Sets light or dark theme.
```typescript
const setTheme = useUIStore((state) => state.setTheme)
setTheme('dark')
setTheme('light')
```

#### toggleSidebar()
Toggles sidebar open/closed.
```typescript
const toggleSidebar = useUIStore((state) => state.toggleSidebar)
toggleSidebar()  // true → false or false → true
```

#### addToast(toast)
Adds notification to queue.
```typescript
const addToast = useUIStore((state) => state.addToast)
addToast({
  message: 'Item added to cart',
  type: 'success',
  duration: 3000
})
```

#### removeToast(toastId)
Removes notification by ID.
```typescript
const removeToast = useUIStore((state) => state.removeToast)
removeToast('toast-123')
```

### Usage in Components
```tsx
import { useUIStore } from '@/store'

function ThemeToggle() {
  const theme = useUIStore((state) => state.theme)
  const setTheme = useUIStore((state) => state.setTheme)
  
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Switch to {theme === 'light' ? 'dark' : 'light'} mode
    </button>
  )
}

function Sidebar() {
  const sidebarOpen = useUIStore((state) => state.sidebarOpen)
  const toggleSidebar = useUIStore((state) => state.toggleSidebar)
  
  return (
    <div>
      <button onClick={toggleSidebar}>Menu</button>
      {sidebarOpen && <nav>Sidebar Content</nav>}
    </div>
  )
}

function ToastContainer() {
  const toasts = useUIStore((state) => state.toasts)
  const removeToast = useUIStore((state) => state.removeToast)
  
  return (
    <div>
      {toasts.map((toast) => (
        <div key={toast.id}>
          <p>{toast.message}</p>
          <button onClick={() => removeToast(toast.id)}>Close</button>
        </div>
      ))}
    </div>
  )
}
```

### Persistence
- **What persists**: Theme only
- **Storage**: localStorage with key `food-store-ui`
- **What does NOT persist**: sidebarOpen, toasts (ephemeral)
- **Why separate**: Theme is user preference, sidebar/toasts are session-specific

### SSR Safety
Like authStore, UIStore includes hydration flag:
```tsx
function App() {
  const hasHydrated = useUIStore((state) => state._hasHydrated)
  
  if (!hasHydrated) return null
  
  return <MainApp />
}
```

---

## Best Practices

### 1. Use Selector Functions
```tsx
// ✅ Good: Only re-renders when selected value changes
const email = useAuthStore((state) => state.user?.email)

// ❌ Bad: Re-renders on any store change
const user = useAuthStore()
```

### 2. Separate Selectors from Actions
```tsx
// ✅ Good: Separate concerns
const username = useAuthStore((state) => state.user?.name)
const logout = useAuthStore((state) => state.logout)

// ❌ Bad: Tight coupling
const { user, logout } = useAuthStore()  // Re-renders when user changes
```

### 3. Don't Create New Objects in Selectors
```tsx
// ✅ Good: Returns primitive
const totalPrice = useCartStore((state) => state.totalPrice())

// ❌ Bad: Creates new object each time
const cartData = useCartStore((state) => ({
  total: state.totalPrice(),
  count: state.totalItems()
}))  // Causes infinite re-renders!
```

### 4. Use Shallow Selector for Multiple Values
```tsx
import { shallow } from 'zustand/react'

// ✅ Good: Shallow comparison prevents unnecessary re-renders
const { theme, sidebarOpen } = useUIStore(
  (state) => ({ theme: state.theme, sidebarOpen: state.sidebarOpen }),
  shallow
)
```

### 5. Handle Hydration in SSR
```tsx
// ✅ Good: Wait for hydration before rendering
function AppRoot() {
  const hasHydrated = useAuthStore((state) => state._hasHydrated)
  
  if (!hasHydrated) {
    return <LoadingSpinner />  // Or null
  }
  
  return <App />
}
```

### 6. Async Actions
```tsx
// ✅ Good: Handle async operations
async function loginUser(email, password) {
  try {
    const response = await api.login(email, password)
    const { accessToken, refreshToken, user } = response.data
    
    useAuthStore.getState().updateTokens(accessToken, refreshToken)
    useAuthStore.getState().setUser(user)
  } catch (error) {
    console.error('Login failed:', error)
  }
}
```

### 7. Integration with Axios
```typescript
// In your Axios interceptor
import axios from 'axios'
import { useAuthStore } from '@/store'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

// Add authorization header
api.interceptors.request.use((config) => {
  const accessToken = useAuthStore.getState().accessToken
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const { refreshToken } = useAuthStore.getState()
      // Refresh token logic here
    }
    return Promise.reject(error)
  }
)
```

---

## Testing Stores

### Unit Tests
```typescript
import { useCartStore } from '@/store'

describe('CartStore', () => {
  beforeEach(() => {
    useCartStore.setState({ items: [] })  // Reset state
  })

  it('should add item to cart', () => {
    const { addItem } = useCartStore.getState()
    addItem({
      productId: 'pizza-1',
      name: 'Pizza',
      price: 10,
      quantity: 1,
    })

    expect(useCartStore.getState().items).toHaveLength(1)
  })
})
```

### Component Tests
```typescript
import { render, screen } from '@testing-library/react'
import { CartSummary } from './CartSummary'
import { useCartStore } from '@/store'

describe('CartSummary', () => {
  it('should display cart total', () => {
    useCartStore.setState({
      items: [
        { productId: 'pizza-1', name: 'Pizza', price: 10, quantity: 2 },
      ],
    })

    render(<CartSummary />)
    expect(screen.getByText(/2 items/)).toBeInTheDocument()
  })
})
```

---

## Troubleshooting

### Issue: Component not re-rendering
**Cause**: Selector returning new object reference  
**Solution**: Use primitive selectors or shallow comparison
```typescript
// ❌ Wrong
const state = useStore((state) => ({ count: state.count }))

// ✅ Correct
const count = useStore((state) => state.count)
```

### Issue: SSR hydration mismatch
**Cause**: Rendering persisted data on server  
**Solution**: Use `_hasHydrated` flag
```typescript
const hasHydrated = useStore((state) => state._hasHydrated)
if (!hasHydrated) return null
```

### Issue: Payment state persisting across reload
**Cause**: Using persist middleware on paymentStore  
**Solution**: paymentStore doesn't use persist (by design)

### Issue: Cart not syncing across tabs
**Cause**: localStorage disabled or private mode  
**Solution**: Check browser settings, persistence may not work in private browsing

---

## Summary

| Store | When to Use | Key Pattern |
|-------|-----------|------------|
| **authStore** | Anywhere you need auth info | Selectors for state, actions for updates |
| **cartStore** | Shopping features, checkout | Items array, computed totals |
| **paymentStore** | Checkout workflow | State machine (step tracking) |
| **uiStore** | Theme, notifications | Multiple ephemeral + one persisted |

For more examples, see `src/store/examples/` directory.
