## ADDED Requirements

### Requirement: paymentStore define el estado completo de la sesión de pago
El store SHALL exportar un hook `usePaymentStore` creado con `create<PaymentState>()()` de Zustand v5, sin persistencia en localStorage, con el estado inicial en `idle`.

#### Scenario: Estado inicial del store
- **WHEN** el store se inicializa (aplicación carga)
- **THEN** `paymentStore` SHALL tener `{ method: null, pedidoId: null, preferenceId: null, pagoId: null, initPoint: null, status: 'idle', error: null }`

#### Scenario: Selección de selector granular evita re-renders
- **WHEN** un componente suscribe solo a `paymentStore.status`
- **THEN** ese componente SHALL re-renderizar ÚNICAMENTE cuando `status` cambia, no cuando `error` u otros campos cambien

### Requirement: paymentStore expone acciones tipadas para cada transición de estado
El store SHALL exponer acciones: `setMethod`, `setPedidoId`, `setPreference`, `setStatus`, `setError`, y `reset`.

#### Scenario: setMethod actualiza el método de pago
- **WHEN** se llama a `setMethod('mercadopago')`
- **THEN** `paymentStore.method` SHALL ser `'mercadopago'`

#### Scenario: setPreference guarda los datos de la preferencia MP
- **WHEN** se llama a `setPreference({ preferenceId: 'pref_123', pagoId: 42, initPoint: 'https://mp.com/...' })`
- **THEN** los tres campos SHALL actualizarse atómicamente en el store

#### Scenario: reset vuelve al estado inicial
- **WHEN** se llama a `reset()`
- **THEN** el store SHALL retornar exactamente al estado inicial `{ method: null, pedidoId: null, preferenceId: null, pagoId: null, initPoint: null, status: 'idle', error: null }`

### Requirement: paymentStore no persiste en localStorage
El store SHALL ser efímero — se resetea al recargar la página o al navegar fuera del checkout.

#### Scenario: Recarga de página limpia el estado de pago
- **WHEN** el usuario recarga la página durante o después de un pago
- **THEN** `paymentStore` SHALL volver al estado inicial (no hay datos de pago guardados)

### Requirement: paymentStore es type-safe con TypeScript strict
El store SHALL definir `PaymentMethod`, `PaymentStatus`, y `PaymentState` como tipos explícitos en `payment.types.ts`, y el store SHALL fallar en compilación si se pasa un valor fuera del union type.

#### Scenario: Intento de setStatus con valor inválido falla en tiempo de compilación
- **WHEN** el código intenta llamar a `setStatus('unknown_status')` donde `'unknown_status'` no está en el union `PaymentStatus`
- **THEN** TypeScript SHALL reportar error de tipo en tiempo de compilación (no en runtime)
