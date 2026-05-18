# Tasks: frontend-payment-checkout-fixes

## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — clases Tailwind v4 para botones, feedback visual, estados disabled/loading
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — accesibilidad WCAG: aria-hidden, aria-live, roles de botones interactivos
- [ ] 0.3 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación Zustand (estado cliente) vs TanStack Query (estado servidor), manejo de errores en mutations
- [ ] 0.4 Leer `.agents/skills/zustand-state-management/README.md` — selectores granulares Zustand v5, uso de useUIStore

---

## 1. BUG 1 — Fix validación de teléfono

### 1.1 Actualizar `validateForm()` en CheckoutPage.tsx

**Archivo**: `frontend/src/pages/CheckoutPage.tsx`

- [ ] 1.1.1 Localizar la función `validateForm()` (línea ~56-76)
- [ ] 1.1.2 Reemplazar el bloque de validación de `telefono_comprador`:

  ```typescript
  // ANTES:
  if (form.telefono_comprador && !/^\d{7,15}$/.test(form.telefono_comprador)) {
    errors.telefono_comprador = 'El teléfono debe tener entre 7 y 15 dígitos'
  }

  // DESPUÉS:
  const telefonoDigits = form.telefono_comprador.replace(/\D/g, '')
  if (form.telefono_comprador.trim() && !/^\d{7,15}$/.test(telefonoDigits)) {
    errors.telefono_comprador = 'El teléfono debe contener entre 7 y 15 dígitos (solo números)'
  }
  ```

- [ ] 1.1.3 Verificar que el campo vacío ('') sigue sin producir error (es opcional)
- [ ] 1.1.4 Verificar que `'abc'` produce error
- [ ] 1.1.5 Verificar que `'123456'` (6 dígitos) produce error
- [ ] 1.1.6 Verificar que `'1234567'` (7 dígitos) no produce error
- [ ] 1.1.7 Verificar que `'+54 11 2345-6789'` (número formateado) normaliza a dígitos antes de validar

---

## 2. BUG 2 — Fix "Preparar pago" no crea pedido ni preferencia

### 2.1 Agregar onError handlers en `handlePay()` de CheckoutPage.tsx

**Archivo**: `frontend/src/pages/CheckoutPage.tsx`

- [ ] 2.1.1 Localizar la función `handlePay()` (línea ~180-210)
- [ ] 2.1.2 Agregar handler `onError` al call de `createOrderMutation.mutate()`:

  ```typescript
  onError: (err) => {
    console.error('[CheckoutPage] createOrder failed:', err)
    setStatus('idle')
    addToast({
      message: 'No se pudo crear el pedido. Revisá tus datos e intentá nuevamente.',
      type: 'error',
    })
  },
  ```

- [ ] 2.1.3 Agregar handler `onError` al call interno de `createPreferenceMutation.mutate()`:

  ```typescript
  onError: (err) => {
    console.error('[CheckoutPage] createPreference failed:', err)
    setStatus('idle')
    addToast({
      message: 'No se pudo generar el pago. Intentá nuevamente.',
      type: 'error',
    })
  },
  ```

- [ ] 2.1.4 Verificar que después de un error el botón "Preparar pago" vuelve a estar habilitado (status vuelve a 'idle')
- [ ] 2.1.5 Verificar que el toast de error es visible al usuario

### 2.2 Quitar `aria-hidden="true"` del botón "Preparar pago"

**Archivo**: `frontend/src/pages/CheckoutPage.tsx`

- [ ] 2.2.1 Localizar el botón con `data-testid="generate-preference-btn"` (línea ~487-499)
- [ ] 2.2.2 Eliminar el atributo `aria-hidden="true"` de ese elemento `<button>`
- [ ] 2.2.3 Verificar que el botón sigue visible y funcional en el DOM

### 2.3 (Observación) Documentar el `direccion_entrega_id: 1` hardcodeado

- [ ] 2.3.1 Asegurarse de que el comentario `// TODO: pick from address selector when available`
      sigue presente y es claro para el próximo desarrollador

  > Nota: No se cambia la lógica de `direccion_entrega_id` en este change —
  > el fix real requeriría un selector de dirección que está fuera del alcance.
  > El fix de onError cubre el síntoma (feedback al usuario cuando falla).

---

## 3. BUG 3 — Deshabilitar CartDrawer en /checkout

### 3.1 Cerrar CartDrawer al montar CheckoutPage

**Archivo**: `frontend/src/pages/CheckoutPage.tsx`

- [ ] 3.1.1 Agregar selector de `setCartDrawerOpen` al inicio del componente:

  ```typescript
  const setCartDrawerOpen = useUIStore((state) => state.setCartDrawerOpen)
  ```

- [ ] 3.1.2 Agregar `useEffect` para cerrar el drawer al montar (antes de los useEffects existentes):

  ```typescript
  // BUG 3 fix: close CartDrawer on checkout mount
  useEffect(() => {
    setCartDrawerOpen(false)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  ```

### 3.2 Retornar null en CartDrawer cuando ruta es /checkout

**Archivo**: `frontend/src/widgets/CartDrawer/CartDrawer.tsx`

- [ ] 3.2.1 Agregar import de `useLocation`:

  ```typescript
  import { Link, useLocation } from 'react-router-dom'
  ```

- [ ] 3.2.2 Al inicio del componente `CartDrawer()`, agregar detección de ruta y early return:

  ```typescript
  const location = useLocation()

  // BUG 3 fix: CartDrawer is disabled on /checkout to prevent cart modification mid-payment
  if (location.pathname === '/checkout') {
    return null
  }
  ```

- [ ] 3.2.3 Verificar que `useLocation` está disponible en el árbol (CartDrawer se renderiza dentro de `<BrowserRouter>` en App.tsx — ya está correctamente ubicado)

### 3.3 Agregar botón "← Volver al carrito" en CheckoutPage

**Archivo**: `frontend/src/pages/CheckoutPage.tsx`

- [ ] 3.3.1 Agregar import de `ArrowLeft` de `lucide-react` (ya instalado):

  ```typescript
  import { ArrowLeft } from 'lucide-react'
  ```

- [ ] 3.3.2 En el bloque `{showForm && (...)}`, dentro del div grid, agregar el botón
      antes del `<h1 className="text-2xl font-bold text-foreground">`:

  ```tsx
  {/* BUG 3 fix: back to cart button */}
  <button
    type="button"
    onClick={() => navigate('/cart')}
    className="mb-4 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded"
  >
    <ArrowLeft className="h-4 w-4" aria-hidden="true" />
    Volver al carrito
  </button>
  ```

- [ ] 3.3.3 Verificar que el botón aparece en la columna izquierda del grid, encima del título
- [ ] 3.3.4 Verificar que hacer click navega a `/cart`
- [ ] 3.3.5 Verificar que el focus ring es visible (accessibility)

---

## 4. Tests

### 4.1 Tests unitarios — validateForm (vitest)

**Archivo nuevo**: `frontend/src/pages/__tests__/CheckoutPage.validateForm.test.ts`
o agregar al test existente si hay uno.

- [ ] 4.1.1 Test: teléfono vacío → sin error (opcional)
- [ ] 4.1.2 Test: teléfono con letras (`'abc'`) → error
- [ ] 4.1.3 Test: teléfono de 6 dígitos → error
- [ ] 4.1.4 Test: teléfono de 7 dígitos → sin error
- [ ] 4.1.5 Test: teléfono de 15 dígitos → sin error
- [ ] 4.1.6 Test: teléfono de 16 dígitos → error
- [ ] 4.1.7 Test: nombre vacío → error
- [ ] 4.1.8 Test: email inválido → error

### 4.2 Tests de integración — CartDrawer (vitest + @testing-library/react)

**Archivo**: `frontend/src/widgets/CartDrawer/__tests__/CartDrawer.test.tsx`

- [ ] 4.2.1 Test: en ruta `/checkout`, CartDrawer retorna null (no se renderiza)
- [ ] 4.2.2 Test: en ruta `/`, CartDrawer se renderiza normalmente
- [ ] 4.2.3 Verificar que el test mocka `useLocation` retornando `{ pathname: '/checkout' }`

---

## 5. Verificación

### 5.1 TypeScript — sin errores de compilación

- [ ] 5.1.1 Ejecutar `npx tsc --noEmit` desde `frontend/`
- [ ] 5.1.2 Corregir cualquier error de tipos antes de continuar

### 5.2 Tests automáticos

- [ ] 5.2.1 Ejecutar `npx vitest run` desde `frontend/`
- [ ] 5.2.2 Verificar que todos los tests pasan (incluyendo los nuevos)
- [ ] 5.2.3 Verificar cobertura frontend >= 40% (si aplica)

### 5.3 Testing manual — BUG 1

- [ ] 5.3.1 Ir a `/checkout` con items en el carrito
- [ ] 5.3.2 Escribir `abc123` en el campo Teléfono
- [ ] 5.3.3 Hacer click en "Preparar pago"
- [ ] 5.3.4 Verificar que aparece el mensaje: "El teléfono debe contener entre 7 y 15 dígitos (solo números)"
- [ ] 5.3.5 Dejar el campo vacío y volver a clickear → verificar que NO aparece error de teléfono
- [ ] 5.3.6 Escribir `1234567890` → verificar que no hay error de teléfono

### 5.4 Testing manual — BUG 2

- [ ] 5.4.1 Con el servidor backend corriendo, completar el formulario correctamente
- [ ] 5.4.2 Seleccionar MercadoPago como método de pago
- [ ] 5.4.3 Hacer click en "Preparar pago"
- [ ] 5.4.4 Verificar en Network tab: `POST /api/v1/pedidos` se dispara
- [ ] 5.4.5 Verificar en Network tab: `POST /api/v1/pagos/crear-preferencia` se dispara tras el éxito del pedido
- [ ] 5.4.6 Si el backend devuelve error: verificar que aparece el toast de error Y el botón vuelve al estado habilitado (no queda spinner infinito)
- [ ] 5.4.7 Verificar que el botón "Preparar pago" NO tiene `aria-hidden="true"` en el DOM (inspeccionar elemento)

### 5.5 Testing manual — BUG 3

- [ ] 5.5.1 Abrir el CartDrawer desde la Navbar (icono carrito)
- [ ] 5.5.2 Navegar a `/checkout` (usando el botón "Proceder al pago" del drawer)
- [ ] 5.5.3 Verificar que el CartDrawer se cerró automáticamente
- [ ] 5.5.4 Verificar que el icono de carrito en la Navbar NO abre el drawer (porque CartDrawer retorna null en /checkout)
- [ ] 5.5.5 Verificar que el botón "← Volver al carrito" es visible encima del título "Finalizar pedido"
- [ ] 5.5.6 Hacer click en "← Volver al carrito" → verificar que navega a `/cart`
- [ ] 5.5.7 Una vez en `/cart`, verificar que el CartDrawer vuelve a funcionar normalmente

**Cuando todos los checks sean ✅, responder exactamente:**
> **"✅ Todo funciona. Aprobado para archivar CHANGE frontend-payment-checkout-fixes"**
