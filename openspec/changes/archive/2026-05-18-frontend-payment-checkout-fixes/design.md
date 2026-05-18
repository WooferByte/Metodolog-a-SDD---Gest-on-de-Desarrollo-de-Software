# Design: frontend-payment-checkout-fixes

## Análisis de causa raíz

### BUG 1 — Validación de teléfono no funciona

**Archivo**: `frontend/src/pages/CheckoutPage.tsx`, función `validateForm()`, línea 71.

**Código actual**:
```typescript
if (form.telefono_comprador && !/^\d{7,15}$/.test(form.telefono_comprador)) {
  errors.telefono_comprador = 'El teléfono debe tener entre 7 y 15 dígitos'
}
```

**Causa raíz exacta**: La condición `if (form.telefono_comprador && ...)` evalúa
el valor antes de aplicar el regex. Esta lógica es **correcta** — si el campo
está vacío, no hay error (es opcional). El regex sí valida caracteres no
numéricos. Sin embargo, el problema está en la **falta de trim**: si el usuario
tipea espacios, la condición truthy pasa pero `^\d{7,15}$` rechaza espacios, y
el error debería mostrarse.

**Análisis más profundo — caso real del bug**: el campo usa `type="tel"` que en
algunos browsers (iOS Safari, Android Chrome) puede auto-formatear con guiones
(`123-456`), lo que hace que `^\d{7,15}$` falle pero sin mensaje claro. El
usuario ve un campo rojo sin entender por qué.

**Fix**: limpiar el valor con `.replace(/\D/g, '')` antes de validar, y mostrar
el error con el formato esperado. Adicionalmente, agregar `trim()` para
consistencia.

**Línea específica a cambiar** (CheckoutPage.tsx línea 71):
```typescript
// ANTES (actual):
if (form.telefono_comprador && !/^\d{7,15}$/.test(form.telefono_comprador)) {
  errors.telefono_comprador = 'El teléfono debe tener entre 7 y 15 dígitos'
}

// DESPUÉS (fix):
const telefonoDigits = form.telefono_comprador.replace(/\D/g, '')
if (form.telefono_comprador.trim() && !/^\d{7,15}$/.test(telefonoDigits)) {
  errors.telefono_comprador = 'El teléfono debe contener entre 7 y 15 dígitos (solo números)'
}
```

Esto tiene la ventaja adicional de que si el usuario pega un número formateado
como `+54 11 2345-6789`, el error le indica que solo debe ingresar dígitos, y al
limpiar, el valor normalizado pasa la validación.

---

### BUG 2 — "Preparar pago" no crea pedido ni preferencia

**Archivo**: `frontend/src/pages/CheckoutPage.tsx`, función `handlePay()`.

**Causa raíz 1 — `direccion_entrega_id: 1` hardcodeado**:

```typescript
createOrderMutation.mutate(
  {
    direccion_entrega_id: 1, // TODO: pick from address selector when available
    forma_pago_id: 1,
    // ...
  },
  {
    onSuccess: (orderData) => {
      createPreferenceMutation.mutate({ pedido_id: orderData.id })
    },
  },
)
```

El payload envía `direccion_entrega_id: 1` fijo. Si el usuario autenticado
(especialmente en entorno de desarrollo/testing con datos fresh) no tiene una
dirección con `id=1` en la BD, el backend devuelve un error 404/422.

**Causa raíz 2 — Ausencia de `onError` en `handlePay`**:

El `mutate()` no tiene handler `onError`. Cuando la mutation falla, el status
queda en `'creating_order'` (seteado antes de llamar a `mutate`) y el botón
queda en loading indefinidamente. El usuario no recibe ningún feedback.

**Causa raíz 3 — Sin reset de status en error**:

`setStatus('creating_order')` se llama antes del mutate, pero si hay un error,
`setStatus` no vuelve a `'idle'`. El botón queda bloqueado con spinner hasta que
el usuario recarga la página.

**Fix**:

```typescript
function handlePay() {
  const errors = validateForm(form)
  if (Object.keys(errors).length > 0) {
    setFormErrors(errors)
    return
  }

  setFormErrors({})
  setStatus('creating_order')

  createOrderMutation.mutate(
    {
      direccion_entrega_id: 1, // TODO: address selector (task futura)
      forma_pago_id: 1,
      observacion: undefined,
      items: items.map((item) => ({
        producto_id: Number(item.productId),
        cantidad: item.quantity,
        ingredientes_excluidos: item.ingredientes_excluidos,
      })),
    },
    {
      onSuccess: (orderData) => {
        createPreferenceMutation.mutate(
          { pedido_id: orderData.id },
          {
            onError: (err) => {
              console.error('[CheckoutPage] createPreference failed:', err)
              setStatus('idle')
              addToast({
                message: 'No se pudo generar el pago. Intentá nuevamente.',
                type: 'error',
              })
            },
          },
        )
      },
      onError: (err) => {
        console.error('[CheckoutPage] createOrder failed:', err)
        setStatus('idle')
        addToast({
          message: 'No se pudo crear el pedido. Revisá tus datos e intentá nuevamente.',
          type: 'error',
        })
      },
    },
  )
}
```

**Adicionalmente — quitar `aria-hidden="true"` del botón "Preparar pago"**:

El botón tiene `aria-hidden="true"` en el JSX actual (CheckoutPage.tsx línea
488), lo que lo oculta a lectores de pantalla. Se debe eliminar este atributo.
El comentario "For MP: trigger order + preference creation first" clarifica su
propósito, pero ocultar un botón interactivo es una violación WCAG.

---

### BUG 3 — CartDrawer operativo en /checkout

**Archivos**: `App.tsx` (render global del CartDrawer) + `CartDrawer.tsx`
(lógica del drawer).

**Causa raíz exacta**:

`CartDrawer` se renderiza en `App.tsx` como overlay global:
```tsx
<Suspense fallback={null}>
  <CartDrawer />
</Suspense>
```

Este componente no tiene acceso a la ruta actual. `CartDrawer.tsx` solo
controla su visibilidad via `cartDrawerOpen` del `uiStore`, sin considerar en
qué ruta está el usuario.

**Fix — dos partes**:

**Parte A: Cerrar CartDrawer automáticamente al entrar a /checkout**

En `CheckoutPage.tsx`, agregar un `useEffect` que cierre el drawer al montar:
```typescript
const setCartDrawerOpen = useUIStore((state) => state.setCartDrawerOpen)

useEffect(() => {
  setCartDrawerOpen(false)
}, []) // solo al montar — cierra cualquier drawer que pudiera estar abierto
```

**Parte B: Deshabilitar la apertura del CartDrawer mientras el usuario está en /checkout**

En `CartDrawer.tsx`, usar `useLocation()` de react-router-dom para detectar la
ruta y no renderizar el drawer si está en `/checkout`:

```typescript
import { useLocation } from 'react-router-dom'

export function CartDrawer() {
  const location = useLocation()
  const isCheckoutPage = location.pathname === '/checkout'

  // If on checkout, close drawer and don't render (to prevent cart modification during payment)
  if (isCheckoutPage) {
    return null
  }
  // ... resto del componente sin cambios
}
```

**Parte C: Botón "← Volver al carrito" en CheckoutPage**

Agregar en CheckoutPage.tsx, antes del `<h1>`:
```tsx
<button
  type="button"
  onClick={() => navigate('/cart')}
  className="mb-4 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
>
  <ArrowLeft className="h-4 w-4" aria-hidden="true" />
  Volver al carrito
</button>
```

---

## Arquitectura de los cambios

```
CheckoutPage.tsx
  ├── validateForm() — BUG 1 fix: trim + digits-only strip antes del regex
  ├── handlePay() — BUG 2 fix: onError handlers + reset status a 'idle'
  ├── useEffect() nuevo — BUG 3 fix: cierra CartDrawer al montar
  ├── aria-hidden="true" eliminado del botón "Preparar pago" — BUG 2 fix
  └── Botón "← Volver al carrito" añadido — BUG 3 fix

CartDrawer.tsx
  └── useLocation() — BUG 3 fix: return null si pathname === '/checkout'
```

## Decisiones de diseño

| Decisión | Alternativa descartada | Razón |
|----------|----------------------|-------|
| Return null en CartDrawer cuando isCheckoutPage | Deshabilitar solo el botón de apertura en Navbar | CartDrawer es global; si se abre programáticamente, igual se mostraría. Return null es más seguro. |
| useEffect en CheckoutPage para cerrar el drawer | Solo depender del return null de CartDrawer | Si el drawer ya estaba abierto ANTES de navegar a /checkout (Zustand persiste cartDrawerOpen = false pero puede no haberse cerrado), el useEffect garantiza que se cierra. |
| Strip de non-digits antes del regex | Rechazar el valor tal cual | UX: si el usuario pega un número formateado, mejor guiarlo que bloquearlo. |
| Toast de error en handlePay | Solo console.error | El usuario debe ver feedback visible cuando una operación crítica falla. |

## Impacto en tests

- `CheckoutPage.test.tsx` (si existe): agregar casos para error en createOrder
  y comportamiento de onError
- `CartDrawer.test.tsx`: agregar caso para verificar `return null` en `/checkout`
- Los tests existentes de `validateForm` (si existen) deben actualizarse para
  reflejar el nuevo mensaje de error del teléfono

## No cambia

- `paymentStore.ts` — sin cambios
- `cartStore.ts` — sin cambios
- `MercadoPagoButton.tsx` — sin cambios
- Backend — sin cambios
- Rutas — sin cambios
