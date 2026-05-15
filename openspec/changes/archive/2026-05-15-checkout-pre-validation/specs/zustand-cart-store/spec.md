## MODIFIED Requirements

### Requirement: CartStore manages shopping cart items

The cartStore SHALL maintain an array of cart items, where each item includes product ID, quantity, price snapshot at time of adding (`precio_carrito`), current display price (`precio`), and personalization data (excluded ingredients).

#### Scenario: Initial empty cart

- **WHEN** application first loads
- **THEN** cartStore.items is empty array

#### Scenario: Add product to cart

- **WHEN** user calls cartStore.addItem({ productoId: 5, cantidad: 2, precio: 150.00 })
- **THEN** new item is added to items array with productoId, cantidad, precio, precio_carrito (set to precio at add time), and ingredientes_excluidos

#### Scenario: precio_carrito is frozen at add time

- **WHEN** a product is added to the cart with precio 150.00
- **THEN** item.precio_carrito is 150.00 and does NOT change even if the product price changes later in the same session

#### Scenario: Prevent duplicate items

- **WHEN** user adds same product twice
- **THEN** quantity is incremented instead of creating duplicate entry
- **THEN** precio_carrito remains the value from the FIRST add (not overwritten)

#### Scenario: Update item quantity

- **WHEN** user calls cartStore.updateQuantity(productId, newQuantity)
- **THEN** item quantity is updated to new value

#### Scenario: Remove item from cart

- **WHEN** user calls cartStore.removeItem(productId)
- **THEN** item removed from items array

#### Scenario: Clear entire cart

- **WHEN** user calls cartStore.clearCart()
- **THEN** items array becomes empty

## ADDED Requirements

### Requirement: CartStore CartItem type includes precio_carrito

The `CartItem` TypeScript interface SHALL include a `precio_carrito: number` field in addition to the existing `precio` field. Both fields are required and SHALL be populated by `addItem()`.

#### Scenario: CartItem shape includes precio_carrito

- **WHEN** an item is retrieved from cartStore.items
- **THEN** it has both `precio: number` (current display price) and `precio_carrito: number` (price at time of add)

#### Scenario: Backward compatibility for pre-existing localStorage items

- **WHEN** cartStore loads from localStorage and an item lacks `precio_carrito`
- **THEN** the store falls back to using `precio` as `precio_carrito` for that item (no crash, no data loss)
