/**
 * Store Type Definitions
 * 
 * This file defines all TypeScript interfaces used across the Zustand stores.
 * Provides type safety and IDE autocomplete for state and actions.
 */

/**
 * AuthStore - JWT token management, user data, role helpers
 * 
 * Persists: accessToken only (refreshToken never stored in localStorage)
 * Use case: Authentication state, JWT token management, user roles
 */
export interface AuthStore {
  // State
  accessToken: string | null
  refreshToken: string | null
  user: {
    id: string
    email: string
    name: string
    roles: string[]
  } | null
  isAuthenticated: boolean
  _hasHydrated: boolean

  // Actions
  updateTokens: (accessToken: string, refreshToken: string) => void
  setUser: (user: AuthStore['user']) => void
  logout: () => void
  setHasHydrated: (hydrated: boolean) => void

  // Helpers
  hasRole: (role: string) => boolean
}

/**
 * CartItem - Individual item in shopping cart
 */
export interface CartItem {
  productId: string
  name: string
  /** Current display price — may change after the product is added to cart. */
  price: number
  /**
   * Price frozen at the moment addItem() is called.
   *
   * Set once when the product is first added. NOT overwritten on subsequent
   * addItem() calls for the same product (duplicate-add only increments quantity).
   * Used by the checkout pre-validation hook to detect price drift against the
   * current backend price (see useCheckoutValidation).
   *
   * Backward-compat: items rehydrated from localStorage before this field was
   * added will lack precio_carrito. The checkout hook falls back to `price`.
   */
  precio_carrito?: number
  quantity: number
  image?: string
  ingredientes_excluidos?: number[] // Ingredient personalization — IDs as integers (RN-CR04/05, aligns with backend INTEGER[])
}

/**
 * CartStore - Shopping cart with persistence
 * 
 * Persists: All items with quantities and personalization
 * Use case: Shopping cart state, item management, price calculations
 */
export interface CartStore {
  // State
  items: CartItem[]

  // Actions
  addItem: (item: CartItem) => void
  removeItem: (productId: string) => void
  updateQuantity: (productId: string, quantity: number) => void
  clearCart: () => void
  getItem: (productId: string) => CartItem | undefined

  // Computed selectors (available as methods)
  totalItems: () => number
  totalPrice: () => number
}

/**
 * PaymentStore - Checkout workflow state
 * 
 * Persists: NOTHING (zero persistence for security)
 * Use case: Multi-step payment/checkout process
 */
export interface PaymentStore {
  // State
  checkoutStep: 'cart' | 'shipping' | 'payment' | 'confirmation'
  preferenceId: string | null
  paymentStatus: 'idle' | 'processing' | 'completed' | 'failed'

  // Actions
  startCheckout: () => void
  setPreference: (preferenceId: string) => void
  updatePaymentStatus: (status: PaymentStore['paymentStatus']) => void
  resetPayment: () => void
}

/**
 * UIStore - UI preferences and notifications
 * 
 * Persists: theme only (sidebar and toasts are ephemeral)
 * Use case: Theme switching, sidebar visibility, toast notifications
 */
export interface UIStore {
  // State
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  cartDrawerOpen: boolean
  toasts: Array<{
    id: string
    message: string
    type: 'success' | 'error' | 'info' | 'warning'
    duration?: number
  }>
  _hasHydrated: boolean

  // Actions
  setTheme: (theme: UIStore['theme']) => void
  toggleSidebar: () => void
  toggleCartDrawer: () => void
  setCartDrawerOpen: (open: boolean) => void
  addToast: (toast: Omit<UIStore['toasts'][0], 'id'>) => void
  removeToast: (toastId: string) => void
  setHasHydrated: (hydrated: boolean) => void
}
