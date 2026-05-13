/**
 * CartStore - Shopping cart with item management and persistence
 *
 * Features:
 * - Add/remove/update cart items
 * - Support for ingredient personalization (ingredientes_excluidos)
 * - Computed selectors: totalItems(), totalPrice()
 * - Full persistence to localStorage with key "food-store-cart"
 * - Survives across page reloads, tab closes, and logout/login
 * - Redux DevTools integration via devtools middleware
 *
 * Usage:
 * ```typescript
 * const items = useCartStore((state) => state.items)
 * const totalPrice = useCartStore((state) => state.totalPrice())
 * const addItem = useCartStore((state) => state.addItem)
 * const removeItem = useCartStore((state) => state.removeItem)
 * ```
 */

import { create } from 'zustand'
import { persist, createJSONStorage, devtools } from 'zustand/middleware'
import type { CartStore, CartItem } from './types'

/**
 * Create cartStore with TypeScript support, localStorage persistence, and devtools.
 *
 * Middleware order (Zustand v5): devtools(persist(...))
 * - devtools wraps persist so Redux DevTools sees the full state tree
 * - persist handles rehydration from localStorage
 *
 * Important: Uses create<T>()() double parentheses for middleware compatibility
 */
export const useCartStore = create<CartStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        items: [],

        // Action: Add item or increment quantity if already exists
        addItem: (item: CartItem) =>
          set((state) => {
            const existingItem = state.items.find(
              (i) => i.productId === item.productId,
            )

            if (existingItem) {
              // Item already in cart - increment quantity
              return {
                items: state.items.map((i) =>
                  i.productId === item.productId
                    ? { ...i, quantity: i.quantity + item.quantity }
                    : i,
                ),
              }
            }

            // New item - add to cart
            return {
              items: [...state.items, item],
            }
          }),

        // Action: Remove item from cart by productId
        removeItem: (productId: string) =>
          set((state) => ({
            items: state.items.filter((i) => i.productId !== productId),
          })),

        // Action: Update quantity of specific item
        // If quantity <= 0, item is removed
        updateQuantity: (productId: string, quantity: number) =>
          set((state) => {
            if (quantity <= 0) {
              return {
                items: state.items.filter((i) => i.productId !== productId),
              }
            }

            return {
              items: state.items.map((i) =>
                i.productId === productId ? { ...i, quantity } : i,
              ),
            }
          }),

        // Action: Clear entire cart
        clearCart: () => set({ items: [] }),

        // Selector: Get item by productId
        getItem: (productId: string) => {
          const state = get()
          return state.items.find((i) => i.productId === productId)
        },

        // Computed: Total number of items (sum of quantities)
        totalItems: () => {
          const state = get()
          return state.items.reduce((sum, item) => sum + item.quantity, 0)
        },

        // Computed: Total price (sum of price * quantity for each item)
        totalPrice: () => {
          const state = get()
          return state.items.reduce(
            (sum, item) => sum + item.price * item.quantity,
            0,
          )
        },
      }),
      {
        name: 'food-store-cart', // unique key in localStorage
        storage: createJSONStorage(() => localStorage),
        // Persist all items with quantities and personalization
        partialize: (state) => ({
          items: state.items,
        }),
      },
    ),
    { name: 'CartStore' },
  ),
)
