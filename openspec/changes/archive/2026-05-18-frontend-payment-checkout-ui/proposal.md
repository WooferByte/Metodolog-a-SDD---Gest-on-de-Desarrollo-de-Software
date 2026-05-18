## Why

El backend de pagos MercadoPago está completo (`payments-mercadopago-integration-backend`, archivado a39c0b4), pero no existe ninguna interfaz de usuario que permita al comprador iniciar el pago. El usuario actualmente no puede completar la compra: el carrito existe en Zustand pero no hay página `/checkout` ni flujo de pago. Este change cierra esa brecha crítica al agregar la UI completa de checkout con integración al SDK de MercadoPago cargado desde CDN.

## What Changes

- **Nueva página** `/checkout` (`CheckoutPage`) — formulario de datos del comprador + resumen del pedido + selector de método de pago + botón de pago MP.
- **Nuevo componente** `PaymentMethodSelector` — selector visual (Tarjeta / Efectivo / MercadoPago) con validación de disponibilidad por monto.
- **Nuevo componente** `MercadoPagoButton` — botón que carga el SDK de MP desde CDN, crea la preferencia llamando a `POST /api/v1/pagos/crear-preferencia`, y abre el modal nativo de MP Checkout.
- **Nuevo componente** `PaymentStatusModal` — modal de confirmación o error post-pago con CTA de redirect.
- **Nuevo store Zustand** `paymentStore` — maneja el estado de la sesión de pago actual (preferenceId, pagoId, método, estado, errores).
- **Nueva ruta** `/checkout` registrada en el router con `ProtectedRoute` (requiere autenticación de rol CLIENT).
- **Tests E2E** Playwright: seleccionar método, rellenar formulario, abrir modal MP, simular pago exitoso y fallido.
- **Tests unitarios** vitest: paymentStore acciones y selectores.

## Capabilities

### New Capabilities

- `checkout-page`: Flujo completo de la página de checkout — resumen del carrito, formulario de datos, selector de método, botón de pago, y redirect post-pago a `/orders/{id}`.
- `mercadopago-sdk-integration`: Carga del SDK de MercadoPago desde CDN (`https://sdk.mercadopago.com/js/v2`), inicialización con la public key, apertura del modal de pago nativo (brickless flow), y manejo de callbacks de resultado.
- `payment-store`: Store Zustand v5 tipado para el estado cliente del flujo de pago — método seleccionado, preferenceId, pagoId, estado del pago, errores, y acciones de reset/update.
- `payment-method-selector`: Componente que permite seleccionar entre métodos de pago disponibles. Cada método tiene icono, label, descripción y estado habilitado/deshabilitado. Persiste la selección en paymentStore.

### Modified Capabilities

- `pedidos`: Al crear el pedido desde el checkout, se llama a `POST /api/v1/pedidos` antes de crear la preferencia de pago. El checkout coordina ambas llamadas secuencialmente.

## Impact

**Frontend:**
- Nueva carpeta `frontend/src/features/payments/` con hooks, components, constants, types.
- Nueva página `frontend/src/pages/CheckoutPage.tsx`.
- Nuevo store `frontend/src/store/paymentStore.ts`.
- Nueva ruta `/checkout` en `frontend/src/app/router.tsx` (o equivalente).
- `frontend/index.html` — agregar `<script src="https://sdk.mercadopago.com/js/v2"></script>` en `<head>`.

**Variables de entorno:**
- `VITE_MP_PUBLIC_KEY` — ya existe en `.env.example`, debe estar configurada en `.env`.

**Sin cambios de backend:** El backend de pagos ya está completo. Este change es 100% frontend.

**Dependencias externas:**
- SDK MercadoPago v2 (CDN, no npm) — `window.MercadoPago` disponible globalmente post-carga.
- NO instalar `@mercadopago/sdk-js` (regla del proyecto).
