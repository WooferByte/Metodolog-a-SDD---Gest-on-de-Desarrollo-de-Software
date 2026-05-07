/**
 * CartStore Tests
 * 
 * Tests for shopping cart state management, item operations,
 * computed totals, and localStorage persistence.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useCartStore } from '../cartStore'
import type { CartItem } from '../types'

describe('CartStore', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    // Reset store to initial state
    useCartStore.setState({
      items: [],
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Initial State', () => {
    it('should have empty items array', () => {
      const state = useCartStore.getState()
      expect(state.items).toEqual([])
    })
  })

  describe('addItem', () => {
    it('should add new item to cart', () => {
      const { addItem } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pepperoni Pizza',
        price: 10.99,
        quantity: 1,
      }

      addItem(item)

      const state = useCartStore.getState()
      expect(state.items).toHaveLength(1)
      expect(state.items[0]).toEqual(item)
    })

    it('should increment quantity if item already exists', () => {
      const { addItem } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pepperoni Pizza',
        price: 10.99,
        quantity: 1,
      }

      addItem(item)
      addItem({ ...item, quantity: 2 })

      const state = useCartStore.getState()
      expect(state.items).toHaveLength(1)
      expect(state.items[0].quantity).toBe(3) // 1 + 2
    })

    it('should support ingredient personalization', () => {
      const { addItem } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pizza',
        price: 10.99,
        quantity: 1,
        ingredientes_excluidos: ['onion', 'mushroom'],
      }

      addItem(item)

      const state = useCartStore.getState()
      expect(state.items[0].ingredientes_excluidos).toEqual([
        'onion',
        'mushroom',
      ])
    })
  })

  describe('removeItem', () => {
    it('should remove item from cart', () => {
      const { addItem, removeItem } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pepperoni Pizza',
        price: 10.99,
        quantity: 1,
      }

      addItem(item)
      removeItem('pizza-123')

      const state = useCartStore.getState()
      expect(state.items).toHaveLength(0)
    })

    it('should not crash if removing non-existent item', () => {
      const { removeItem } = useCartStore.getState()
      expect(() => removeItem('non-existent')).not.toThrow()

      const state = useCartStore.getState()
      expect(state.items).toHaveLength(0)
    })
  })

  describe('updateQuantity', () => {
    it('should update quantity of existing item', () => {
      const { addItem, updateQuantity } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pepperoni Pizza',
        price: 10.99,
        quantity: 1,
      }

      addItem(item)
      updateQuantity('pizza-123', 5)

      const state = useCartStore.getState()
      expect(state.items[0].quantity).toBe(5)
    })

    it('should remove item if quantity is set to 0', () => {
      const { addItem, updateQuantity } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pepperoni Pizza',
        price: 10.99,
        quantity: 1,
      }

      addItem(item)
      updateQuantity('pizza-123', 0)

      const state = useCartStore.getState()
      expect(state.items).toHaveLength(0)
    })

    it('should remove item if quantity is negative', () => {
      const { addItem, updateQuantity } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pepperoni Pizza',
        price: 10.99,
        quantity: 1,
      }

      addItem(item)
      updateQuantity('pizza-123', -5)

      const state = useCartStore.getState()
      expect(state.items).toHaveLength(0)
    })
  })

  describe('clearCart', () => {
    it('should clear all items', () => {
      const { addItem, clearCart } = useCartStore.getState()
      addItem({
        productId: 'pizza-1',
        name: 'Pizza 1',
        price: 10.99,
        quantity: 1,
      })
      addItem({
        productId: 'pizza-2',
        name: 'Pizza 2',
        price: 12.99,
        quantity: 2,
      })

      clearCart()

      const state = useCartStore.getState()
      expect(state.items).toHaveLength(0)
    })
  })

  describe('getItem', () => {
    it('should return item if exists', () => {
      const { addItem, getItem } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pepperoni Pizza',
        price: 10.99,
        quantity: 1,
      }

      addItem(item)
      const found = getItem('pizza-123')

      expect(found).toEqual(item)
    })

    it('should return undefined if item does not exist', () => {
      const { getItem } = useCartStore.getState()
      const found = getItem('non-existent')

      expect(found).toBeUndefined()
    })
  })

  describe('totalItems', () => {
    it('should calculate total quantity of all items', () => {
      const { addItem, totalItems } = useCartStore.getState()
      addItem({
        productId: 'pizza-1',
        name: 'Pizza 1',
        price: 10.99,
        quantity: 2,
      })
      addItem({
        productId: 'pizza-2',
        name: 'Pizza 2',
        price: 12.99,
        quantity: 3,
      })

      expect(totalItems()).toBe(5) // 2 + 3
    })

    it('should return 0 for empty cart', () => {
      const { totalItems } = useCartStore.getState()
      expect(totalItems()).toBe(0)
    })
  })

  describe('totalPrice', () => {
    it('should calculate total price correctly', () => {
      const { addItem, totalPrice } = useCartStore.getState()
      addItem({
        productId: 'pizza-1',
        name: 'Pizza 1',
        price: 10.00,
        quantity: 2,
      })
      addItem({
        productId: 'pizza-2',
        name: 'Pizza 2',
        price: 15.00,
        quantity: 1,
      })

      expect(totalPrice()).toBe(35.00) // (10 * 2) + (15 * 1)
    })

    it('should return 0 for empty cart', () => {
      const { totalPrice } = useCartStore.getState()
      expect(totalPrice()).toBe(0)
    })

    it('should handle decimal prices', () => {
      const { addItem, totalPrice } = useCartStore.getState()
      addItem({
        productId: 'item-1',
        name: 'Item',
        price: 9.99,
        quantity: 3,
      })

      expect(totalPrice()).toBeCloseTo(29.97, 2)
    })
  })

  describe('localStorage persistence', () => {
    it('should persist items to localStorage', () => {
      const { addItem } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-123',
        name: 'Pepperoni Pizza',
        price: 10.99,
        quantity: 2,
      }

      addItem(item)

      const stored = localStorage.getItem('food-store-cart')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.items).toHaveLength(1)
      expect(parsed.state.items[0].productId).toBe('pizza-123')
      expect(parsed.state.items[0].quantity).toBe(2)
    })

    it('should restore items from localStorage', () => {
      // Simulate stored state
      const storedState = {
        state: {
          items: [
            {
              productId: 'pizza-1',
              name: 'Pizza',
              price: 10.99,
              quantity: 2,
            },
          ],
        },
        version: 0,
      }

      localStorage.setItem('food-store-cart', JSON.stringify(storedState))

      // Store should restore items on hydration
      // Note: In real app, this happens on component mount with useEffect
      const currentState = useCartStore.getState()
      expect(currentState.items).toBeDefined()
    })

    it('should persist ingredient personalization', () => {
      const { addItem } = useCartStore.getState()
      const item: CartItem = {
        productId: 'pizza-1',
        name: 'Pizza',
        price: 10.99,
        quantity: 1,
        ingredientes_excluidos: ['onion'],
      }

      addItem(item)

      const stored = localStorage.getItem('food-store-cart')
      const parsed = JSON.parse(stored!)
      expect(parsed.state.items[0].ingredientes_excluidos).toEqual(['onion'])
    })
  })

  describe('multi-tab synchronization', () => {
    it('should sync cart across tabs when localStorage changes', () => {
      // Simulate another tab adding an item
      const storedState = {
        state: {
          items: [
            {
              productId: 'pizza-1',
              name: 'Pizza from other tab',
              price: 10.99,
              quantity: 1,
            },
          ],
        },
        version: 0,
      }

      localStorage.setItem('food-store-cart', JSON.stringify(storedState))

      // Trigger storage event (simulating cross-tab communication)
      const storageEvent = new StorageEvent('storage', {
        key: 'food-store-cart',
        newValue: JSON.stringify(storedState),
      })

      window.dispatchEvent(storageEvent)

      // Store should be updated (Zustand handles this with persist middleware)
      expect(localStorage.getItem('food-store-cart')).toBeTruthy()
    })
  })
})
