## ADDED Requirements

### Requirement: CartStore manages shopping cart items

The cartStore SHALL maintain an array of cart items, where each item includes product ID, quantity, price snapshot, and personalization data (excluded ingredients).

#### Scenario: Initial empty cart
- **WHEN** application first loads
- **THEN** cartStore.items is empty array

#### Scenario: Add product to cart
- **WHEN** user calls cartStore.addItem({ productoId: 5, cantidad: 2 })
- **THEN** new item is added to items array with productoId, cantidad, precio_snapshot, and ingredientes_excluidos

#### Scenario: Prevent duplicate items
- **WHEN** user adds same product twice
- **THEN** quantity is incremented instead of creating duplicate entry

#### Scenario: Update item quantity
- **WHEN** user calls cartStore.updateQuantity(productId, newQuantity)
- **THEN** item quantity is updated to new value

#### Scenario: Remove item from cart
- **WHEN** user calls cartStore.removeItem(productId)
- **THEN** item removed from items array

#### Scenario: Clear entire cart
- **WHEN** user calls cartStore.clearCart()
- **THEN** items array becomes empty

### Requirement: CartStore computes cart totals

The cartStore SHALL provide computed selectors for totalItems() and totalPrice() without storing redundant data.

#### Scenario: Calculate total items
- **WHEN** cart has 2 units of product A and 3 units of product B
- **THEN** totalItems() returns 5

#### Scenario: Calculate total price
- **WHEN** cart contains items with prices [10.00, 20.00, 15.00]
- **THEN** totalPrice() returns 45.00

#### Scenario: Get single item
- **WHEN** user calls getItem(productId)
- **THEN** returns item object or undefined if not found

### Requirement: CartStore persists items to localStorage

The cartStore SHALL automatically save and restore cart items from localStorage across page reloads.

#### Scenario: Persist cart items
- **WHEN** user adds items and closes browser
- **THEN** cartStore uses localStorage key "food-store-cart" to save items

#### Scenario: Restore cart after reload
- **WHEN** page reloads
- **THEN** cartStore restores items from localStorage automatically

#### Scenario: Cart survives logout
- **WHEN** user logs out and logs back in
- **THEN** cart items remain in localStorage

### Requirement: CartStore supports personalization

The cartStore SHALL allow storing excluded ingredients per cart item for personalized purchases.

#### Scenario: Add personalized item
- **WHEN** user adds item with excluded ingredients [1, 3, 7]
- **THEN** item stored with ingredientes_excluidos array

#### Scenario: Retrieve personalization
- **WHEN** cart item is rendered
- **THEN** component can access ingredientes_excluidos to show customization

