## ADDED Requirements

### Requirement: Two-column desktop layout for cart page
La página `/cart` SHALL renderizar un layout de dos columnas en viewport `lg` (1024px+): columna izquierda con la lista de ítems (flexible) y columna derecha con el panel de resumen (ancho fijo de 380px). En viewport menor a `lg`, el layout SHALL colapsar a una sola columna con la lista arriba y el resumen debajo.

#### Scenario: Desktop two-column layout
- **WHEN** el usuario navega a `/cart` con viewport >= 1024px y el carrito tiene ítems
- **THEN** la página muestra dos columnas: ítems a la izquierda y OrderSummary a la derecha (380px)

#### Scenario: Mobile single-column layout
- **WHEN** el usuario navega a `/cart` con viewport < 1024px y el carrito tiene ítems
- **THEN** la página muestra una sola columna: lista de ítems arriba, OrderSummary debajo

### Requirement: Sticky order summary panel on desktop
El panel de `OrderSummary` SHALL mantenerse visible (sticky) mientras el usuario hace scroll por la lista de ítems en desktop. El panel SHALL usar `position: sticky; top: 1rem` y solo aplicarse en layout de dos columnas.

#### Scenario: Panel stays visible while scrolling items
- **WHEN** la lista de ítems es más larga que el viewport en desktop
- **THEN** el panel de resumen permanece visible mientras el usuario scrollea la lista

#### Scenario: No sticky on mobile
- **WHEN** el viewport es < 1024px
- **THEN** el panel de resumen no es sticky — forma parte del flujo normal de scroll

### Requirement: Cart page header with clear cart action
La página `/cart` SHALL mostrar un heading `<h1>Mi carrito</h1>` y un botón "Vaciar carrito" visible solo cuando el carrito tiene ítems. El botón SHALL tener un estilo de texto con color destructivo en hover.

#### Scenario: Clear cart button visible with items
- **WHEN** el carrito tiene al menos un ítem
- **THEN** el botón "Vaciar carrito" es visible en el header

#### Scenario: Clear cart button hidden when empty
- **WHEN** el carrito está vacío
- **THEN** el botón "Vaciar carrito" NO es visible
