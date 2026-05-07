/**
 * Example: CartStore Usage
 * 
 * Demonstrates how to use the cartStore to manage shopping cart items,
 * quantities, and totals with ingredient personalization.
 */

import { useCartStore } from '@/store'
import type { CartItem } from '@/store'

/**
 * ShoppingCart Component
 * 
 * Shows how to:
 * - Display cart items
 * - Calculate and show totals
 * - Update quantities
 * - Remove items
 */
export function ShoppingCartExample() {
  const items = useCartStore((state) => state.items)
  const totalItems = useCartStore((state) => state.totalItems)
  const totalPrice = useCartStore((state) => state.totalPrice)
  const updateQuantity = useCartStore((state) => state.updateQuantity)
  const removeItem = useCartStore((state) => state.removeItem)
  const clearCart = useCartStore((state) => state.clearCart)

  if (items.length === 0) {
    return <div>Your cart is empty</div>
  }

  return (
    <div>
      <h2>Shopping Cart</h2>
      <p>Items: {totalItems()}</p>
      <p>Total: ${totalPrice().toFixed(2)}</p>

      <ul>
        {items.map((item) => (
          <li key={item.productId}>
            <h3>{item.name}</h3>
            <p>Price: ${item.price}</p>
            <p>
              Quantity:
              <input
                type="number"
                min="1"
                value={item.quantity}
                onChange={(e) =>
                  updateQuantity(item.productId, parseInt(e.target.value))
                }
              />
            </p>
            {item.ingredientes_excluidos && item.ingredientes_excluidos.length > 0 && (
              <p>Excluded: {item.ingredientes_excluidos.join(', ')}</p>
            )}
            <button onClick={() => removeItem(item.productId)}>Remove</button>
          </li>
        ))}
      </ul>

      <button onClick={clearCart}>Clear Cart</button>
    </div>
  )
}

/**
 * AddToCart Component
 * 
 * Shows how to:
 * - Create cart items with personalization
 * - Add items to cart
 * - Handle ingredient exclusions
 */
export function AddToCartExample() {
  const addItem = useCartStore((state) => state.addItem)

  const handleAddPizza = () => {
    const item: CartItem = {
      productId: 'pizza-001',
      name: 'Pepperoni Pizza',
      price: 12.99,
      quantity: 1,
      image: '/pizza.jpg',
      ingredientes_excluidos: ['onion'], // User can customize
    }

    addItem(item)
  }

  return (
    <div>
      <button onClick={handleAddPizza}>Add Pizza to Cart</button>
    </div>
  )
}

/**
 * CartSummary Component
 * 
 * Shows how to:
 * - Display mini cart summary
 * - Use computed selectors
 * - Show badge with item count
 */
export function CartSummaryExample() {
  const totalItems = useCartStore((state) => state.totalItems)
  const totalPrice = useCartStore((state) => state.totalPrice)

  return (
    <div>
      <span>
        Cart: {totalItems()} items | ${totalPrice().toFixed(2)}
      </span>
    </div>
  )
}
