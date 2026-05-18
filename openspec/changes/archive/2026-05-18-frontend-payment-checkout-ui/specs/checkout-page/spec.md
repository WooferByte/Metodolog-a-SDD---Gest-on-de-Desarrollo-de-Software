## ADDED Requirements

### Requirement: CheckoutPage muestra resumen del carrito y formulario del comprador
La página `/checkout` SHALL renderizar el resumen del carrito activo (items, subtotal, total) y un formulario con los datos del comprador (nombre completo, email, teléfono opcional) antes de mostrar las opciones de pago.

#### Scenario: Carrito vacío redirige al catálogo
- **WHEN** el usuario navega a `/checkout` con el carrito vacío (0 items)
- **THEN** el sistema SHALL redirigir automáticamente a `/` con un mensaje toast "Tu carrito está vacío"

#### Scenario: Carrito con items muestra el resumen correctamente
- **WHEN** el usuario navega a `/checkout` con al menos 1 item en el carrito
- **THEN** el sistema SHALL mostrar el nombre, cantidad y precio de cada item, el subtotal calculado, y el total final

#### Scenario: Usuario sin autenticación es redirigido
- **WHEN** un usuario no autenticado navega a `/checkout`
- **THEN** el sistema SHALL redirigir a `/login` (ProtectedRoute behavior)

### Requirement: CheckoutPage valida el formulario antes de permitir el pago
El formulario del comprador SHALL validar los campos requeridos en el cliente antes de habilitar el botón de pago.

#### Scenario: Formulario incompleto deshabilita el botón de pago
- **WHEN** el campo `nombre_comprador` está vacío o tiene menos de 3 caracteres
- **THEN** el botón de pago SHALL permanecer deshabilitado (`disabled` y `aria-disabled="true"`)

#### Scenario: Email con formato inválido muestra error inline
- **WHEN** el usuario ingresa un email sin formato válido en el campo `email_comprador`
- **THEN** el sistema SHALL mostrar un mensaje de error debajo del campo (`role="alert"`) sin enviar el formulario

#### Scenario: Formulario completo habilita el botón de pago
- **WHEN** `nombre_comprador` tiene al menos 3 caracteres y `email_comprador` tiene formato válido
- **THEN** el botón de pago SHALL estar habilitado y responder a clicks

### Requirement: CheckoutPage coordina la creación del pedido y la preferencia de pago
Al confirmar el pago, la página SHALL crear primero el pedido vía `POST /api/v1/pedidos` y luego la preferencia de pago vía `POST /api/v1/pagos/crear-preferencia`.

#### Scenario: Creación exitosa del pedido y preferencia
- **WHEN** el usuario hace click en el botón de pago con el formulario válido
- **THEN** el sistema SHALL (1) crear el pedido con estado `PENDIENTE`, (2) obtener el `pedido_id`, (3) crear la preferencia de pago con ese `pedido_id`, (4) guardar `preference_id` y `pago_id` en `paymentStore`, (5) abrir el modal de MP

#### Scenario: Error al crear el pedido
- **WHEN** la llamada a `POST /api/v1/pedidos` retorna un error (4xx o 5xx)
- **THEN** el sistema SHALL mostrar un toast de error con el detalle del problema y NO continuar con la preferencia de pago

#### Scenario: Error al crear la preferencia de pago
- **WHEN** el pedido se crea con éxito pero `POST /api/v1/pagos/crear-preferencia` retorna error
- **THEN** el sistema SHALL mostrar un toast de error y actualizar `paymentStore.status` a `'error'`

### Requirement: CheckoutPage muestra el estado del pago post-callback de MercadoPago
Cuando MercadoPago redirige de vuelta a la app con query params de resultado, la página SHALL detectar el resultado y mostrar el modal apropiado.

#### Scenario: Pago exitoso redirige a la orden
- **WHEN** la URL contiene `?payment=success&pedido_id={id}`
- **THEN** el sistema SHALL actualizar `paymentStore.status` a `'success'`, mostrar `PaymentStatusModal` en modo éxito, y ofrecer un botón "Ver mi pedido" que navega a `/orders/{id}`

#### Scenario: Pago fallido muestra modal de error con opción de reintento
- **WHEN** la URL contiene `?payment=failure&pedido_id={id}`
- **THEN** el sistema SHALL mostrar `PaymentStatusModal` en modo error con mensaje "El pago no pudo procesarse" y botones "Intentar de nuevo" (que reabre el flujo de pago para el mismo `pedido_id`) y "Cancelar"

#### Scenario: Pago pendiente muestra modal informativo
- **WHEN** la URL contiene `?payment=pending&pedido_id={id}`
- **THEN** el sistema SHALL mostrar `PaymentStatusModal` en modo pendiente con mensaje "Tu pago está siendo procesado" e instrucciones sobre cuándo se confirmará
