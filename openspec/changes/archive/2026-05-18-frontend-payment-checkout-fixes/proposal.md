# Proposal: frontend-payment-checkout-fixes

## Qué

Corregir tres bugs críticos detectados durante el testing manual del change
`frontend-payment-checkout-ui`, que impiden completar el flujo de pago de forma
confiable.

### Bug 1 — Validación de teléfono no muestra error

**Síntoma**: al tipear caracteres no numéricos en el campo Teléfono y hacer
click en "Preparar pago", el error de validación no aparece porque el campo
es opcional y la condición de validación tiene un falsy short-circuit que
silencia el error.

**Archivo afectado**: `frontend/src/pages/CheckoutPage.tsx` — función
`validateForm()`, línea 71.

### Bug 2 — "Preparar pago" no crea el pedido ni la preferencia

**Síntoma**: hacer click en "Preparar pago" no dispara `POST /api/v1/pedidos`
ni `POST /api/v1/pagos/crear-preferencia`.

**Causas raíz identificadas en el código**:

1. **`showForm` bloquea la renderización del botón**: la condición
   `showForm` en `CheckoutPage.tsx` requiere que `validationResult` sea
   truthy Y que `modalOpen` sea false. Si la validación retorna con
   `confirmedDespiteWarnings = false` y ninguna advertencia, `showForm`
   puede ser `false` en el momento en que el usuario presiona el botón
   (race condition entre mutations).

2. **`direccion_entrega_id: 1` hardcodeado**: si el usuario autenticado
   no tiene una dirección con id=1 en la base de datos, el backend devuelve
   422/404 y la mutation falla silenciosamente (sin toast de error visible
   al usuario).

3. **Ausencia de feedback visual de error**: cuando `createOrderMutation`
   falla, el status queda en `'creating_order'` y el botón queda en
   loading indefinidamente. No hay `onError` handler en el `mutate()` call
   de `handlePay()`.

4. **El botón "Preparar pago" tiene `aria-hidden="true"`**: este atributo
   oculta el botón a lectores de pantalla y puede interferir con algunas
   herramientas de testing.

### Bug 3 — CartDrawer sigue operativo en /checkout

**Síntoma**: en `/checkout`, el CartDrawer global (renderizado en `App.tsx`
fuera del árbol de rutas) permanece operativo. El usuario puede abrir el
drawer, modificar el carrito (agregar/quitar items), y eso rompe el flujo
de checkout porque el total visible en el resumen no refleja el carrito real.

**Causa raíz**: `CartDrawer` se renderiza en `App.tsx` como overlay global
sin tener en cuenta la ruta actual. No existe ningún mecanismo para
desactivarlo o cerrarlo automáticamente cuando el usuario navega a
`/checkout`.

Además no hay un botón "← Volver al carrito" en CheckoutPage que permita
al usuario salir limpiamente.

## Por qué es crítico

- **Bug 2** es un bloqueante total: impide crear pedidos, que es la función
  core del flujo de pago.
- **Bug 3** introduce inconsistencias de estado que pueden causar pedidos con
  ítems incorrectos.
- **Bug 1** degrada la experiencia: datos de contacto potencialmente inválidos
  llegan al backend.

## Qué cambia

| Archivo | Cambio |
|---------|--------|
| `frontend/src/pages/CheckoutPage.tsx` | Fix Bug 1 (validación teléfono), Fix Bug 2 (onError handler + feedback), Fix Bug 3 (botón volver al carrito) |
| `frontend/src/widgets/CartDrawer/CartDrawer.tsx` | Fix Bug 3: detectar ruta `/checkout` y cerrar/deshabilitar drawer automáticamente |
| `frontend/src/pages/CheckoutPage.tsx` | Quitar `aria-hidden="true"` del botón "Preparar pago" |

## Alcance

- Solo frontend
- No requiere cambios de backend ni migración Alembic
- No agrega dependencias nuevas
- El change padre `frontend-payment-checkout-ui` queda en estado 54/60 tasks
  (no se archiva hasta que estos fixes pasen)

## Change de referencia

`frontend-payment-checkout-ui` — change original del que surgen estos bugs.
