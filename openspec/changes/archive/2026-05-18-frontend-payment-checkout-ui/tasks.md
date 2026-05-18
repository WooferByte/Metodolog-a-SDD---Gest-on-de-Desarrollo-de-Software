## 0. Skills

- [x] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — componentes con CVA, Tailwind v4, tokens, animaciones para el formulario y selector de método
- [x] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — accesibilidad WCAG AA, ARIA patterns para formulario y modal de pago
- [x] 0.3 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — bundle optimization, carga diferida del SDK de MP, re-render optimization en el store
- [x] 0.4 Leer `.agents/skills/zustand-state-management/README.md` — create<T>()() syntax, async actions, selector pattern para paymentStore
- [x] 0.5 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación Zustand (client state) vs TanStack Query (server state), evitar duplicación
- [x] 0.6 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — addInitScript para auth, mockear backend MP, simular pago exitoso/fallido
- [x] 0.7 Leer `.agents/skills/web-payments/SKILL.md` — principios de seguridad en pagos (server-side, idempotencia, manejo de todos los estados)

## 1. Tipos y Store

- [x] 1.1 Crear `frontend/src/features/payments/types/payment.types.ts` — definir `PaymentMethod` union type (`'mercadopago' | 'cash' | null`), `PaymentStatus` union type (`'idle' | 'creating_order' | 'creating_preference' | 'waiting_payment' | 'success' | 'error' | 'pending'`), e interface `PaymentState` con todos los campos del store
- [x] 1.2 Crear `frontend/src/store/paymentStore.ts` — store Zustand v5 con `create<PaymentState>()()`, sin persist middleware, acciones: `setMethod`, `setPedidoId`, `setPreference`, `setStatus`, `setError`, `reset`. Verificar que no hay persistencia en localStorage.
- [x] 1.3 Agregar declaración global de TypeScript para `window.MercadoPago` en `frontend/src/features/payments/types/payment.types.ts` o en `frontend/src/vite-env.d.ts` — `declare global { interface Window { MercadoPago: any } }`
- [x] 1.4 Crear `frontend/src/features/payments/constants/paymentMethods.ts` — array de `PaymentMethodOption` con `{ id, label, description, icon, enabled }` para los 3 métodos (MercadoPago: enabled, Tarjeta: disabled, Efectivo: disabled)

## 2. Hooks de TanStack Query

- [x] 2.1 Crear `frontend/src/features/payments/hooks/useCreateOrder.ts` — `useMutation` que llama a `POST /api/v1/pedidos` con los datos del carrito y el comprador. Devuelve `{ pedido_id }`. En `onSuccess`: llama a `paymentStore.setPedidoId(pedido_id)`.
- [x] 2.2 Crear `frontend/src/features/payments/hooks/useCreatePreference.ts` — `useMutation` que llama a `POST /api/v1/pagos/crear-preferencia` con `{ pedido_id }`. Devuelve `{ init_point, preference_id, pago_id }`. En `onSuccess`: llama a `paymentStore.setPreference(...)` y `paymentStore.setStatus('waiting_payment')`.
- [x] 2.3 Crear `frontend/src/features/payments/hooks/usePaymentStatus.ts` — `useQuery` que llama a `GET /api/v1/pagos/{pedido_id}/status`. Solo se activa cuando `pedidoId !== null` y `status === 'waiting_payment'`. Usado como verificación post-redirect.

## 3. Componente PaymentMethodSelector

- [x] 3.1 Crear `frontend/src/features/payments/components/PaymentMethodSelector.tsx` — renderizar `role="radiogroup"` con `aria-label="Método de pago"`. Cada opción con `role="radio"`, `aria-checked`, `aria-disabled`. Leer opciones de `paymentMethods.ts`.
- [x] 3.2 Implementar lógica de selección: click en opción habilitada → `setMethod(method)` + limpiar `preferenceId/pagoId/initPoint` del store. Click en deshabilitada → ignorar.
- [x] 3.3 Implementar navegación por teclado (flechas para moverse entre opciones, skip de deshabilitadas) según WCAG radiogroup pattern.
- [x] 3.4 Implementar indicador visual de selección con Tailwind v4 — borde y fondo diferenciado para la opción seleccionada vs no seleccionada vs deshabilitada.
- [x] 3.5 Escribir tests unitarios en `frontend/src/features/payments/components/__tests__/PaymentMethodSelector.test.tsx` — renderización, click en habilitada, click en deshabilitada (ignorado), indicador visual de selección.

## 4. Componente MercadoPagoButton

- [x] 4.1 Crear `frontend/src/features/payments/components/MercadoPagoButton.tsx` — verificar `typeof window.MercadoPago !== 'undefined'` al montar. Si no disponible: renderizar botón deshabilitado con mensaje.
- [x] 4.2 Implementar inicialización del SDK: `new window.MercadoPago(import.meta.env.VITE_MP_PUBLIC_KEY, { locale: 'es-AR' })`. Guardar instancia en `useRef`. Cleanup en useEffect return.
- [x] 4.3 Implementar handler del botón: verificar que `paymentStore.preferenceId !== null`, llamar a `mp.checkout({ preference: { id: preferenceId }, autoOpen: true })`, actualizar `paymentStore.status` a `'waiting_payment'`.
- [x] 4.4 Implementar estados visuales del botón: idle (habilitado), loading spinner (durante `creating_order` / `creating_preference`), disabled (sin preferenceId o SDK no disponible). Usar `aria-busy` y `aria-disabled`.
- [x] 4.5 Escribir tests unitarios en `frontend/src/features/payments/components/__tests__/MercadoPagoButton.test.tsx` — mockear `window.MercadoPago`, verificar estados del botón, verificar llamada al SDK con preferenceId.

## 5. Componente PaymentStatusModal

- [x] 5.1 Crear `frontend/src/features/payments/components/PaymentStatusModal.tsx` — modal que se muestra cuando `paymentStore.status` es `'success'`, `'error'`, o `'pending'`. Usar Radix Dialog primitive (`@radix-ui/react-dialog`) o un `<dialog>` nativo con manejo de focus trap.
- [x] 5.2 Implementar modo **success**: ícono de check verde, mensaje "¡Pago exitoso!", botón "Ver mi pedido" que navega a `/orders/{pedidoId}` y llama a `paymentStore.reset()` y `cartStore.clear()`.
- [x] 5.3 Implementar modo **error**: ícono de error rojo, mensaje "El pago no pudo procesarse", botón "Intentar de nuevo" (llama a `useCreatePreference` con el `pedidoId` existente para generar nueva preferencia), botón "Cancelar" (navega a `/` y llama a `paymentStore.reset()`).
- [x] 5.4 Implementar modo **pending**: ícono de reloj, mensaje "Tu pago está siendo procesado. Te notificaremos cuando se confirme.", botón "Ver mis pedidos" que navega a `/orders`.
- [x] 5.5 Asegurar WCAG AA: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` apuntando al título, focus trap dentro del modal, cierre con Escape.
- [x] 5.6 Escribir tests unitarios en `frontend/src/features/payments/components/__tests__/PaymentStatusModal.test.tsx` — renderización de los 3 modos, click en "Ver mi pedido", click en "Intentar de nuevo".

## 6. Página CheckoutPage

- [x] 6.1 Crear `frontend/src/pages/CheckoutPage.tsx` — estructura en dos columnas en desktop (formulario izquierda, resumen carrito derecha), una columna en mobile. Usar `Container` y clases Tailwind v4 responsive.
- [x] 6.2 Implementar resumen del carrito: leer `cartStore` para mostrar items (nombre, cantidad, precio unitario), subtotal, y total. Si carrito vacío: redirect a `/` con toast.
- [x] 6.3 Implementar formulario del comprador con estado local (`useState`): campos `nombre_comprador` (required, min 3), `email_comprador` (required, formato email), `telefono_comprador` (optional, 7-15 dígitos). Validación inline con mensajes de error `role="alert"`.
- [x] 6.4 Integrar `PaymentMethodSelector` y leer `paymentStore.method` para mostrar el botón de pago correspondiente (solo `MercadoPagoButton` por ahora).
- [x] 6.5 Implementar el handler del botón de pago: (1) validar formulario, (2) setear `paymentStore.setStatus('creating_order')`, (3) llamar `useCreateOrder.mutate(...)`, en `onSuccess` llamar `useCreatePreference.mutate({ pedido_id })`.
- [x] 6.6 Implementar detección de query params al montar (`useSearchParams`): si `?payment=success&pedido_id=X`, setear `paymentStore.status='success'` y `paymentStore.setPedidoId(X)`. Si `?payment=failure`, setear `status='error'`. Si `?payment=pending`, setear `status='pending'`.
- [x] 6.7 Integrar `PaymentStatusModal` — se renderiza condicionalmente cuando `paymentStore.status` es `'success'`, `'error'`, o `'pending'`.

## 7. Configuración de SDK y Ruta

- [x] 7.1 Agregar en `frontend/index.html` dentro de `<head>`: `<script src="https://sdk.mercadopago.com/js/v2" defer></script>`
- [x] 7.2 Verificar que `VITE_MP_PUBLIC_KEY` está en `frontend/.env.example`. Si no existe la variable, agregarla con valor placeholder `TEST-xxxx`.
- [x] 7.3 Registrar la ruta `/checkout` en el router de la aplicación (`frontend/src/app/router.tsx` o equivalente) envuelta en `ProtectedRoute` que requiera autenticación (rol CLIENT).
- [x] 7.4 Agregar link o botón "Finalizar compra" en el componente del carrito (si existe) que navegue a `/checkout`.

## 8. Tests E2E Playwright

- [x] 8.1 Verificar que Playwright está instalado en el proyecto (`frontend/playwright.config.ts` existe). Si no, instalar `@playwright/test` y crear la config según la skill `testing-e2e-playwright`.
- [x] 8.2 Crear `frontend/e2e/checkout/checkout-flow.spec.ts` — test: navegar a `/checkout` sin autenticación → redirige a `/login`.
- [x] 8.3 Agregar test: navegar a `/checkout` con auth CLIENT y carrito vacío → redirige a `/` con toast.
- [x] 8.4 Crear `frontend/e2e/checkout/payment-method.spec.ts` — test: autenticado con carrito con items → seleccionar "MercadoPago" → verificar que el botón de pago MP se habilita.
- [x] 8.5 Agregar test: intentar seleccionar método deshabilitado ("Tarjeta") → verificar que `paymentStore.method` NO cambia.
- [x] 8.6 Crear `frontend/e2e/checkout/mercadopago-payment.spec.ts` — test simulando pago exitoso: mockear `POST /api/v1/pedidos` → retorna `{ id: 99 }`, mockear `POST /api/v1/pagos/crear-preferencia` → retorna `{ preference_id: 'pref_test', pago_id: 1, init_point: 'https://mp.com' }`, mockear `window.MercadoPago` (spy), navegar a `/checkout?payment=success&pedido_id=99` → verificar modal éxito visible y botón "Ver mi pedido".
- [x] 8.7 Agregar test simulando pago fallido: navegar a `/checkout?payment=failure&pedido_id=99` → verificar modal error visible, botón "Intentar de nuevo" presente.
- [x] 8.8 Agregar test de formulario inválido: dejar `nombre_comprador` vacío, hacer click en botón de pago → verificar mensaje de error visible y que `POST /api/v1/pedidos` NO fue llamado.

## 9. Tests Unitarios del Store

- [x] 9.1 Crear `frontend/src/store/__tests__/paymentStore.test.ts` — test: estado inicial correcto, `setMethod` actualiza method, `setPreference` actualiza los 3 campos atómicamente, `reset` vuelve al estado inicial.
- [x] 9.2 Agregar test: setStatus con valor fuera del union type no compila (verificar via TypeScript `// @ts-expect-error`).
- [x] 9.3 Agregar test: selección granular — suscriptor a `status` no re-renderiza cuando cambia `error` (test de selector aislado).

## 10. Verificación Final

- [x] 10.1 Correr `cd frontend && npx tsc --noEmit` — sin errores de TypeScript.
- [x] 10.2 Correr `cd frontend && npx vitest run` — todos los tests unitarios pasan.
- [ ] 10.3 Correr `cd frontend && npm run lint` — sin errores de lint. (script no existe en el proyecto)
- [ ] 10.4 Correr tests E2E: `cd frontend && npx playwright test e2e/checkout/` — todos los tests E2E pasan. (requiere server corriendo)
- [ ] 10.5 Verificar responsive en mobile (375px) y desktop (1280px) — formulario y resumen se muestran correctamente en ambos.
- [ ] 10.6 Verificar ARIA con herramientas de DevTools: `PaymentMethodSelector` tiene `role="radiogroup"`, opciones tienen `role="radio"` y `aria-checked`. `PaymentStatusModal` tiene `role="dialog"` y `aria-modal="true"`.
- [ ] 10.7 Verificar en Swagger (`http://localhost:8000/docs`) que los endpoints `POST /api/v1/pagos/crear-preferencia` y `GET /api/v1/pagos/{pedido_id}/status` responden correctamente.
- [ ] 10.8 Leer `post-change-verification` skill en `.agents/skills/post-change-verification/SKILL.md` y ejecutar el health check completo.
