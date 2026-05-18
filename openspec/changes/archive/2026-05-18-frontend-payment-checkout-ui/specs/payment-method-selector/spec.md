## ADDED Requirements

### Requirement: PaymentMethodSelector muestra los métodos de pago disponibles
El componente SHALL renderizar una lista de métodos de pago con icono, label y descripción breve. Para el MVP, solo MercadoPago está habilitado; los demás se muestran como `disabled` con label "(Próximamente)".

#### Scenario: Renderizado de métodos disponibles
- **WHEN** el componente monta
- **THEN** SHALL mostrar al menos 3 opciones: "MercadoPago" (habilitado), "Tarjeta de crédito/débito" (deshabilitado), "Efectivo" (deshabilitado)

#### Scenario: Método deshabilitado no es seleccionable
- **WHEN** el usuario hace click en un método marcado como `disabled`
- **THEN** el sistema SHALL ignorar el click y no actualizar `paymentStore.method`

### Requirement: PaymentMethodSelector actualiza paymentStore al seleccionar un método
Al hacer click en un método habilitado, el componente SHALL llamar a `usePaymentStore.getState().setMethod(method)`.

#### Scenario: Selección de MercadoPago
- **WHEN** el usuario hace click en la opción "MercadoPago"
- **THEN** `paymentStore.method` SHALL ser `'mercadopago'` y la opción SHALL mostrar indicador visual de selección (borde/fondo destacado)

#### Scenario: Cambio de método resetea la preferencia anterior
- **WHEN** el usuario cambia de método después de haber seleccionado uno previamente
- **THEN** el sistema SHALL llamar a `setMethod(newMethod)` y limpiar `preferenceId`, `pagoId`, `initPoint` para evitar usar una preferencia de un método anterior

### Requirement: PaymentMethodSelector cumple con WCAG AA
El componente SHALL usar `role="radiogroup"` en el contenedor y `role="radio"` en cada opción, con `aria-checked` y `aria-disabled` apropiados.

#### Scenario: Navegación por teclado entre métodos
- **WHEN** el foco está en el selector y el usuario presiona las teclas de flecha
- **THEN** el foco SHALL moverse entre las opciones de método disponibles (skip de deshabilitados)

#### Scenario: Estado seleccionado anunciado por screen reader
- **WHEN** "MercadoPago" está seleccionado
- **THEN** el elemento SHALL tener `aria-checked="true"` y el screen reader SHALL anunciar "MercadoPago, seleccionado"
