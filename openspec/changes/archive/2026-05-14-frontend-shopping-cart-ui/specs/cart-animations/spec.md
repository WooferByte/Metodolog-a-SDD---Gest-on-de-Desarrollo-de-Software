## ADDED Requirements

### Requirement: Smooth transitions on cart item modifications
Todos los cambios visuales en los componentes del carrito (hover states, color transitions, opacity changes) SHALL usar `transition-colors` o `transition-opacity` con `duration-200`. No SHALL haber cambios de estado bruscos sin transición en elementos interactivos.

#### Scenario: Button hover transitions
- **WHEN** el usuario hace hover sobre cualquier botón del carrito (eliminar, agregar, QuantityStepper)
- **THEN** el cambio de color ocurre con transición suave de 200ms

#### Scenario: Card hover border transition
- **WHEN** el usuario hace hover sobre un CartItemRow
- **THEN** el borde del card cambia con transición suave

### Requirement: CartDrawer slide animation
El `CartDrawer` SHALL entrar y salir con una animación de slide horizontal desde la derecha. La transición SHALL usar `transform: translateX` con `duration-300 ease-in-out`. SHALL usarse `transition-transform` (no `transition-all`) para evitar repaint de propiedades costosas.

#### Scenario: Drawer opens with slide animation
- **WHEN** el usuario abre el CartDrawer
- **THEN** el drawer desliza desde fuera del viewport derecho hacia su posición visible, tomando ~300ms

#### Scenario: Drawer closes with slide animation
- **WHEN** el usuario cierra el CartDrawer
- **THEN** el drawer desliza de vuelta fuera del viewport hacia la derecha, tomando ~300ms

### Requirement: Backdrop fade animation on CartDrawer
El overlay/backdrop del `CartDrawer` SHALL hacer fade-in al abrir y fade-out al cerrar, usando `transition-opacity duration-300`.

#### Scenario: Backdrop fades in
- **WHEN** el CartDrawer se abre
- **THEN** el overlay oscuro hace fade-in suave

#### Scenario: Backdrop fades out
- **WHEN** el CartDrawer se cierra
- **THEN** el overlay hace fade-out antes de ser removido del DOM

### Requirement: Entry animation for new cart items
Los nuevos `CartItemRow` agregados al carrito (visibles tanto en CartPage como en CartDrawer) SHALL tener una animación de entrada sutil: fade-in + slide desde arriba de 8px hacia su posición. La animación SHALL durar ~200ms y ocurrir solo al aparecer el ítem por primera vez.

#### Scenario: New item enters with animation
- **WHEN** un nuevo ítem es agregado al carrito mientras la lista es visible
- **THEN** el ítem aparece con transición de opacity 0→1 y translateY -8px→0

#### Scenario: Existing items are not re-animated
- **WHEN** se modifica la cantidad de un ítem ya existente
- **THEN** los otros ítems no reproducen la animación de entrada
