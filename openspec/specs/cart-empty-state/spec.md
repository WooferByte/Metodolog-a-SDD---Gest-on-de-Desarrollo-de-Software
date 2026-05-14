## ADDED Requirements

### Requirement: Food-store themed empty cart illustration
El componente `EmptyCart` SHALL mostrar una ilustración SVG con estética de food store (plato, tenedor, carrito o similar). La ilustración SHALL usar `currentColor` para respetar los tokens de tema, SHALL tener `aria-hidden="true"` (decorativa), y SHALL tener dimensiones de al menos 128×128px.

#### Scenario: Illustration visible in empty state
- **WHEN** el carrito está vacío
- **THEN** se muestra una ilustración SVG de food store, centrada, opacidad suave

#### Scenario: Illustration is decorative
- **WHEN** el screen reader lee la página
- **THEN** la ilustración es ignorada (aria-hidden="true")

### Requirement: Warm emotional messaging in empty state
El componente `EmptyCart` SHALL mostrar un heading `<h2>` con texto cálido orientado a food store (ej. "Tu carrito está vacío") y un párrafo descriptivo que invite al usuario a explorar los productos.

#### Scenario: Heading and description present
- **WHEN** el carrito está vacío
- **THEN** se muestra un h2 con mensaje principal y párrafo con subtexto descriptivo

### Requirement: CTA to catalog from empty state
El componente `EmptyCart` SHALL mostrar un botón/link primario con texto claro (ej. "Ver productos" o "Explorar el menú") que navega a `/catalog`. El CTA SHALL incluir un ícono relevante (ej. flecha, carrito, comida) de lucide-react.

#### Scenario: CTA navigates to catalog
- **WHEN** el usuario hace click en el CTA del estado vacío
- **THEN** la navegación lleva a `/catalog`

#### Scenario: CTA is keyboard accessible
- **WHEN** el usuario navega con teclado y llega al CTA
- **THEN** el CTA es activable con Enter y tiene focus ring visible
