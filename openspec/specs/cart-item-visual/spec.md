## ADDED Requirements

### Requirement: Prominent product image in cart item row
Cada `CartItemRow` SHALL mostrar la imagen del producto con dimensiones mínimas de 96×96px en desktop y 80×80px en mobile. La imagen SHALL tener `object-fit: cover`, bordes redondeados, y un fallback visual (ícono de comida) cuando la imagen no esté disponible o falle al cargar.

#### Scenario: Image displayed correctly
- **WHEN** el ítem tiene `image` definido y la URL es válida
- **THEN** se muestra la imagen con tamaño 96×96 en desktop, `object-cover`, bordes redondeados

#### Scenario: Fallback when image fails
- **WHEN** el ítem no tiene `image` o la URL produce error
- **THEN** se muestra un placeholder con ícono de comida y fondo `bg-muted`

### Requirement: Ingredient exclusions shown with descriptive labels
Las personalizaciones activas (ingredientes excluidos) SHALL mostrarse como etiquetas pill legibles. Dado que `ingredientes_excluidos` contiene IDs numéricos, las etiquetas SHALL mostrar el texto "Sin ingrediente" (genérico) hasta que se resuelvan los nombres. El número de exclusiones activas SHALL ser visible para el usuario.

#### Scenario: No exclusions
- **WHEN** `ingredientes_excluidos` está vacío o es `undefined`
- **THEN** no se muestra ninguna etiqueta de personalización

#### Scenario: With active exclusions
- **WHEN** `ingredientes_excluidos` tiene al menos un ID
- **THEN** se muestra una pill por cada exclusión con texto descriptivo, en color `muted`

### Requirement: Per-item subtotal display
Cada `CartItemRow` SHALL mostrar el subtotal del ítem (precio × cantidad) alineado a la derecha, con label "Subtotal:" en texto secundario y valor en texto prominente (`font-semibold`).

#### Scenario: Subtotal calculated correctly
- **WHEN** el ítem tiene precio $500 y cantidad 3
- **THEN** el subtotal muestra "$1.500"

#### Scenario: Subtotal updates with quantity change
- **WHEN** el usuario cambia la cantidad
- **THEN** el subtotal se actualiza inmediatamente sin reload

### Requirement: Item row interactive affordances
Cada `CartItemRow` SHALL tener un borde con efecto hover (`hover:border-ring`) que indique interactividad. El botón de eliminar SHALL cambiar a color destructivo en hover con fondo suave.

#### Scenario: Hover state on card
- **WHEN** el usuario hace hover sobre un CartItemRow
- **THEN** el borde del card cambia a `ring` color con transición suave

#### Scenario: Delete button hover state
- **WHEN** el usuario hace hover sobre el botón de eliminar
- **THEN** el ícono y fondo cambian a color destructivo/10
