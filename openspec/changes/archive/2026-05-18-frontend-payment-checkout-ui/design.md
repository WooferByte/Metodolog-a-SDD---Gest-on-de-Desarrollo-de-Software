## Context

El backend de pagos MercadoPago está operativo con dos endpoints clave: `POST /api/v1/pagos/crear-preferencia` (devuelve `init_point`, `preference_id`, `pago_id`) y `GET /api/v1/pagos/{pedido_id}/status`. El carrito existe como store Zustand en `cartStore` (persistido en localStorage). El proyecto usa React Router DOM v6, Zustand v5, TanStack Query v5, Tailwind v4, y TypeScript strict.

La restricción principal es que el SDK de MercadoPago NO debe instalarse via npm sino cargarse desde el CDN oficial (`https://sdk.mercadopago.com/js/v2`). Esto expone `window.MercadoPago` globalmente. El proyecto sigue FSD estricto (Pages → Widgets → Features → Entities → Shared) y requiere WCAG AA mínimo en todos los componentes de UI.

## Goals / Non-Goals

**Goals:**
- Implementar la página `/checkout` completa con flujo de pago MercadoPago.
- Crear `paymentStore` Zustand v5 para gestionar el estado cliente del pago (método, preferenceId, pagoId, estado, errores).
- Integrar el SDK de MP desde CDN con apertura del modal nativo (brickless flow — sin Bricks, sin reinventar).
- Redirigir a `/orders/{id}` en pago exitoso con el `pedido_id` retornado.
- Manejo de errores con toast + modal visual diferenciado (éxito / error / pendiente).
- Cobertura E2E con Playwright y unitaria con vitest.

**Non-Goals:**
- Implementar métodos de pago alternativos más allá del botón MP (tarjeta directa, efectivo real) — el selector existe pero solo MP está activo en MVP.
- Manejo de webhooks desde el frontend — ya manejado por el backend.
- Panel de administración de pagos — es otro change.
- Persistencia del estado de pago entre sesiones (paymentStore no persiste en localStorage).

## Decisions

### D1: SDK MercadoPago via CDN — carga diferida con useEffect

**Decisión:** Cargar el script del SDK en `index.html` como tag `<script>` en `<head>` con atributo `defer`. Verificar disponibilidad de `window.MercadoPago` en el componente antes de usarlo.

**Alternativas consideradas:**
- `@mercadopago/sdk-js` npm: Descartado. Regla explícita del proyecto (AGENTS.md). Además, el CDN oficial garantiza actualizaciones automáticas del SDK.
- Carga dinámica con `document.createElement('script')` en el componente: Más complejo, introduce race conditions. CDN en `<head>` con `defer` es más simple y confiable.

**Implicación:** Agregar `declare global { interface Window { MercadoPago: any } }` en un archivo de types para satisfacer TypeScript strict.

### D2: Flujo de checkout en 3 pasos secuenciales

**Decisión:** El flujo es: (1) validar carrito no vacío → (2) crear pedido vía `POST /api/v1/pedidos` → (3) crear preferencia MP vía `POST /api/v1/pagos/crear-preferencia` → (4) abrir modal MP con `init_point`.

**Alternativas consideradas:**
- Crear preferencia sin pedido primero: Rechazado. El backend requiere `pedido_id` para crear la preferencia. El pedido debe existir antes.
- Crear pedido al confirmar pago exitoso (callback MP): Rechazado. Si el pago fue exitoso pero la creación del pedido falla, quedamos en estado inconsistente. El pedido debe existir antes con estado `PENDIENTE`.

**Implicación:** El `pedido_id` se guarda en `paymentStore` tan pronto como se crea, para poder redirigir a `/orders/{pedido_id}` en el callback de éxito.

### D3: paymentStore — Zustand v5 sin persistencia

**Decisión:** `paymentStore` gestiona exclusivamente el estado de la sesión de pago actual. No persiste en localStorage. Se resetea al salir de la página de checkout o en pago exitoso (después del redirect).

**Alternativas consideradas:**
- Persistir en localStorage: Innecesario. El pago es una sesión efímera. Si el usuario recarga, vuelve al carrito. Persistir añade complejidad de cleanup.
- Estado local en CheckoutPage con useState: Descartado. El estado de pago necesita ser accesible desde múltiples componentes (MercadoPagoButton, PaymentStatusModal, CheckoutPage) sin prop drilling.

**Estructura del store:**
```typescript
interface PaymentState {
  method: 'mercadopago' | 'cash' | null
  pedidoId: number | null
  preferenceId: string | null
  pagoId: number | null
  initPoint: string | null
  status: 'idle' | 'creating_order' | 'creating_preference' | 'waiting_payment' | 'success' | 'error' | 'pending'
  error: string | null
}
```

### D4: Modal de pago MP — brickless flow con redirect/callback

**Decisión:** Usar `new MercadoPago(publicKey)` y `.checkout({ preference: { id: preferenceId }, autoOpen: true })`. El resultado se detecta via URL params cuando MP redirige de vuelta a la app (success_url, failure_url, pending_url configurados en el backend).

**Alternativas consideradas:**
- MP Bricks (CardPayment Brick): Más personalizable pero requiere más integración con formulario de tarjeta. El backend ya genera preferencias que abren el modal nativo completo. Brickless es suficiente para MVP.
- Polling `GET /api/v1/pagos/{pedido_id}/status`: Se usa como fallback de verificación post-redirect, no como mecanismo principal.

**Implicación:** Las URLs de retorno (`back_urls`) deben configurarse en el backend al crear la preferencia. En el frontend, al llegar a `/checkout?payment=success&pedido_id=X`, redirigir automáticamente a `/orders/X`.

### D5: Arquitectura de componentes — FSD estricto

**Estructura:**
```
frontend/src/
├── features/payments/
│   ├── components/
│   │   ├── PaymentMethodSelector.tsx
│   │   ├── MercadoPagoButton.tsx
│   │   └── PaymentStatusModal.tsx
│   ├── hooks/
│   │   ├── useCreateOrder.ts        # TanStack Query mutation
│   │   ├── useCreatePreference.ts   # TanStack Query mutation
│   │   └── usePaymentStatus.ts      # TanStack Query query (polling)
│   ├── constants/
│   │   └── paymentMethods.ts
│   └── types/
│       └── payment.types.ts
├── store/
│   └── paymentStore.ts
└── pages/
    └── CheckoutPage.tsx
```

**Decisión:** Los hooks de TanStack Query (server state) viven en `features/payments/hooks/`. El store Zustand (client state) vive en `store/paymentStore.ts` (mismo nivel que `cartStore`). `CheckoutPage` en `pages/` coordina todo.

### D6: Validación client-side — nativa sin TanStack Form

**Decisión:** Validación básica con `useState` + lógica de validación inline en el componente de formulario. No instalar TanStack Form en este change.

**Razón:** AGENTS.md indica "Formularios: TanStack Form — instalar cuando llegue el change de formularios". El formulario del checkout es simple (nombre, email, teléfono opcionalmente). No justifica la instalación de una dependencia nueva en este change.

**Campos validados:** nombre_comprador (requerido, min 3 chars), email_comprador (formato email), teléfono_comprador (opcional, si presente: 7-15 dígitos).

### D7: PaymentStatusModal — basado en estado del URL + paymentStore

**Decisión:** El modal se muestra cuando `paymentStore.status` es `'success'`, `'error'`, o `'pending'`. También se activa al detectar query params `?payment=success|failure|pending` en la URL (callback de MP).

**Detección de resultado:**
```typescript
// En CheckoutPage, al montar con query params de MP:
const searchParams = useSearchParams()
const paymentResult = searchParams.get('payment') // 'success' | 'failure' | 'pending'
const pedidoId = searchParams.get('pedido_id')    // id del pedido
```

## Risks / Trade-offs

**[Risk] SDK MP no disponible (CDN bloqueado o script no cargado):** → Verificar `typeof window.MercadoPago !== 'undefined'` antes de instanciar. Si no está disponible, mostrar mensaje de error con instrucción de recargar. El botón MP queda deshabilitado.

**[Risk] El pedido se crea pero el pago falla → pedido queda en estado PENDIENTE:** → El backend ya maneja este caso vía FSM. El pedido en estado `PENDIENTE` puede ser cancelado manualmente o por timeout (si se implementa). El frontend muestra el modal de error con opción "Intentar de nuevo" que no crea un nuevo pedido sino solo una nueva preferencia para el mismo `pedido_id`.

**[Risk] Usuario cierra el modal de MP sin completar el pago:** → El callback de cancelación de MP (si existe) no hace nada. El `pedido_id` persiste en `paymentStore`. El usuario puede reintentar. Si navega fuera, el store se resetea.

**[Risk] Race condition: usuario presiona "Pagar" dos veces:** → El botón queda deshabilitado mientras `status` es `'creating_order'` o `'creating_preference'`. Implementar `disabled` y `aria-disabled` en el botón.

**[Trade-off] No usar MP Bricks:** Menor personalización visual del formulario de tarjeta. El modal nativo de MP tiene su propio diseño que no puede customizarse con Tailwind. Aceptable para MVP — la experiencia de pago de MP es conocida por los usuarios argentinos.

**[Trade-off] `pedido_id` en URL params:** El pedido_id queda expuesto en la URL al volver de MP. Es un ID autoincremental (no secreto) — aceptable. No expone datos sensibles.

## Migration Plan

1. Agregar script CDN de MP en `frontend/index.html`.
2. Crear `paymentStore.ts` en `frontend/src/store/`.
3. Crear feature `frontend/src/features/payments/` con componentes y hooks.
4. Crear `frontend/src/pages/CheckoutPage.tsx`.
5. Registrar ruta `/checkout` en el router con `ProtectedRoute`.
6. Verificar que `VITE_MP_PUBLIC_KEY` está en `.env`.
7. Correr `npx vitest run` — todos los tests existentes deben pasar.
8. Correr tests E2E de Playwright.

**Rollback:** La ruta `/checkout` puede deshabilitarse removiendo el registro en el router. No hay cambios de base de datos en este change.

## Open Questions

- **OQ1:** ¿El backend configura `back_urls` en la preferencia (success/failure/pending apuntando a `/checkout?payment=...`)? Si no, el frontend no recibirá el callback de resultado. → Verificar en `pagos/service.py`.
- **OQ2:** ¿Existe ya un `cartStore` con la estructura del carrito (items, total)? → El change `frontend-orders-management-admin` archivado puede haberlo creado. Verificar antes de implementar la integración.
- **OQ3:** ¿La ruta para crear pedidos es `POST /api/v1/pedidos` y requiere el carrito completo en el body? → Verificar schema del pedido en `backend/pedidos/schemas.py`.
