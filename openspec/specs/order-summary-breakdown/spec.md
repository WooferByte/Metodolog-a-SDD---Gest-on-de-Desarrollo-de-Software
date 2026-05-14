## ADDED Requirements

### Requirement: Itemized cost breakdown in order summary
El `OrderSummary` SHALL mostrar un desglose de costos en tres líneas: (1) Subtotal de productos, (2) Delivery estimado, (3) Total. Cada línea SHALL tener label a la izquierda y valor a la derecha. El total SHALL ser visualmente prominente (`text-xl font-bold`).

#### Scenario: Breakdown with items
- **WHEN** el carrito tiene ítems y el subtotal es menor al umbral de envío gratis
- **THEN** se muestran tres filas: Subtotal, Delivery ($500 estimado), Total

#### Scenario: Breakdown at free delivery threshold
- **WHEN** el subtotal supera $3000
- **THEN** la fila de Delivery muestra "$0" o "Gratis" y el label cambia a color primario/verde

### Requirement: Free delivery badge and progress indicator
El `OrderSummary` SHALL detectar si el subtotal supera el umbral de envío gratis ($3000). Si supera el umbral, SHALL mostrar un badge "Envío gratis". Si no lo supera, SHALL mostrar un indicador de progreso con texto "Te faltan $X para envío gratis".

#### Scenario: Free delivery achieved
- **WHEN** `totalPrice() >= 3000`
- **THEN** se muestra badge con texto "Envío gratis" en color éxito y delivery = $0

#### Scenario: Progress towards free delivery
- **WHEN** `totalPrice() < 3000`
- **THEN** se muestra "Te faltan $X para envío gratis" donde X = 3000 - totalPrice()

### Requirement: High-conversion checkout CTA button
El botón "Proceder al pago" SHALL ser visualmente prominente: ancho completo, padding generoso (`py-3.5`), background de color primario, texto blanco en bold. SHALL mostrar el total en el propio botón para reforzar la decisión. El botón SHALL estar deshabilitado (con opacidad reducida y cursor `not-allowed`) cuando el carrito está vacío.

#### Scenario: CTA with items — authenticated
- **WHEN** el carrito tiene ítems y el usuario está autenticado
- **THEN** el botón navega a `/checkout` y muestra el total en el texto

#### Scenario: CTA with items — unauthenticated
- **WHEN** el carrito tiene ítems y el usuario NO está autenticado
- **THEN** el botón navega a `/login` con `state: { from: { pathname: '/checkout' } }`

#### Scenario: CTA disabled when empty
- **WHEN** el carrito está vacío
- **THEN** el botón está deshabilitado (`aria-disabled="true"`) y no es navegable

### Requirement: Hint text for unauthenticated users
Cuando el carrito tiene ítems y el usuario NO está autenticado, el `OrderSummary` SHALL mostrar una nota de texto pequeño debajo del CTA: "Deberás iniciar sesión para completar el pedido".

#### Scenario: Login hint shown to unauthenticated users
- **WHEN** el carrito tiene ítems y el usuario no está autenticado
- **THEN** se muestra el texto de hint debajo del botón CTA

#### Scenario: No hint when authenticated
- **WHEN** el usuario está autenticado
- **THEN** no se muestra el texto de hint
