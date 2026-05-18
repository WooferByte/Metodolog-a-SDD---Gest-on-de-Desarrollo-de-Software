## ADDED Requirements

### Requirement: SDK de MercadoPago se carga desde CDN oficial
El script `https://sdk.mercadopago.com/js/v2` SHALL cargarse desde `index.html` con atributo `defer` para garantizar disponibilidad antes de que el componente `MercadoPagoButton` lo use.

#### Scenario: SDK disponible en window
- **WHEN** la página de checkout carga y el script CDN se ejecutó correctamente
- **THEN** `typeof window.MercadoPago` SHALL ser `'function'` antes de que el botón MP intente instanciar

#### Scenario: SDK no disponible — botón deshabilitado con mensaje
- **WHEN** `typeof window.MercadoPago === 'undefined'` al renderizar `MercadoPagoButton`
- **THEN** el botón SHALL renderizar como deshabilitado con texto "Pago temporalmente no disponible" y `aria-label` descriptivo

### Requirement: MercadoPagoButton inicializa el SDK con la public key del entorno
El componente SHALL leer `import.meta.env.VITE_MP_PUBLIC_KEY` e instanciar `new window.MercadoPago(publicKey, { locale: 'es-AR' })` una única vez por montaje de componente.

#### Scenario: Instanciación con public key válida
- **WHEN** `VITE_MP_PUBLIC_KEY` está configurada y el SDK está disponible
- **THEN** el componente SHALL instanciar MP y habilitar el botón de pago

#### Scenario: Public key no configurada — error en desarrollo
- **WHEN** `VITE_MP_PUBLIC_KEY` es `undefined` o vacía
- **THEN** el componente SHALL lanzar un `console.error` con mensaje descriptivo y deshabilitar el botón

### Requirement: MercadoPagoButton abre el modal de pago nativo con la preferencia creada
Al hacer click en el botón, el componente SHALL usar `mp.checkout({ preference: { id: preferenceId }, autoOpen: true })` para abrir el modal de pago de MP.

#### Scenario: Click en botón con preferenceId disponible
- **WHEN** `paymentStore.preferenceId` está disponible y el SDK está instanciado
- **THEN** el componente SHALL llamar a `mp.checkout(...)` con `autoOpen: true` y actualizar `paymentStore.status` a `'waiting_payment'`

#### Scenario: Click en botón sin preferenceId — estado de error
- **WHEN** `paymentStore.preferenceId` es `null` al hacer click
- **THEN** el sistema SHALL mostrar toast de error "No se pudo iniciar el pago. Intenta de nuevo." sin llamar al SDK

#### Scenario: Botón deshabilitado durante creación de preferencia
- **WHEN** `paymentStore.status` es `'creating_order'` o `'creating_preference'`
- **THEN** el botón SHALL estar deshabilitado y mostrar un spinner de carga con `aria-busy="true"`

### Requirement: El componente limpia la instancia del SDK al desmontar
Para evitar memory leaks, el componente SHALL limpiar cualquier referencia a la instancia de MP en la función de cleanup del useEffect.

#### Scenario: Cleanup al navegar fuera del checkout
- **WHEN** el usuario navega fuera de la página de checkout (componente se desmonta)
- **THEN** la referencia al objeto MP SHALL establecerse a `null` y no quedar en closure activo
