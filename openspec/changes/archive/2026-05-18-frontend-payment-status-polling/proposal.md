# Proposal: frontend-payment-status-polling

## EPIC
11 — Pagos

## Change anterior
`frontend-payment-checkout-fixes` (commit cd1dfdc)

## Qué

Implementar el hook `usePaymentStatusPolling(pedidoId: number | null)` que consulta
periódicamente el endpoint `GET /api/v1/pagos/{pedido_id}/status` para detectar
cuándo el pago fue confirmado o rechazado por MercadoPago, e integrar este hook
en el componente `PaymentStatusModal` para mostrar feedback visual al usuario
mientras el pago está pendiente.

### Componentes a crear / modificar

| Artefacto | Tipo | Acción |
|-----------|------|--------|
| `frontend/src/features/payments/hooks/usePaymentStatusPolling.ts` | hook | CREAR |
| `frontend/src/features/payments/hooks/__tests__/usePaymentStatusPolling.test.ts` | test (vitest) | CREAR |
| `frontend/src/features/payments/hooks/usePaymentStatus.ts` | hook existente | NO MODIFICAR (ya cubre one-shot query) |
| `frontend/src/store/paymentStore.ts` | store Zustand | NO MODIFICAR (ya tiene `setStatus`, `setError`) |
| `frontend/src/features/payments/types/payment.types.ts` | tipos | EXTENDER si falta `PollingState` |

El hook existente `usePaymentStatus` cubre la verificación one-shot post-redirect.
`usePaymentStatusPolling` cubre el polling activo mientras el modal está visible.

## Por qué

### Problema

Cuando el usuario inicia un pago con MercadoPago y vuelve a la app (ya sea via
redirect automático o cerrando el popup), el estado del pago en el backend puede
tardar segundos o incluso minutos en actualizarse vía webhook. Sin polling,
el usuario no recibe feedback automático y debe recargar la página manualmente.

### Impacto

- **UX rota**: el usuario ve "Pago pendiente" indefinidamente sin saber si se procesó.
- **Soporte innecesario**: usuarios contactan soporte pensando que el pago falló.
- **Pérdida de confianza**: la falta de feedback en pagos genera abandono.

### Solución

Un hook de polling reutilizable que:
1. Consulta `/api/v1/pagos/{pedido_id}/status` cada 30 segundos.
2. Usa `setInterval` con cleanup en `useEffect` return (sin TanStack Query
   `refetchInterval` — el polling debe continuar aunque la query sea `stale`
   y debe detenerse por lógica de negocio, no por caché).
3. Se detiene automáticamente cuando `mp_status !== 'pending'`.
4. Implementa retry exponencial en caso de error de red (máx. 3 reintentos: 1s, 2s, 4s).
5. Actualiza `paymentStore.status` cuando el estado cambia.

### Justificación de no usar `refetchInterval` de TanStack Query

`refetchInterval` es controlado por el cache y no permite lógica de parada basada
en el contenido de la respuesta sin `refetchIntervalInBackground`. Además, el hook
existente `usePaymentStatus` ya usa TanStack Query para la verificación one-shot.
El polling continuo es estado de proceso (cliente), no estado servidor — corresponde
a Zustand + `useEffect` según la arquitectura del proyecto.

## Criterios de aceptación

- [ ] Hook `usePaymentStatusPolling` exportado desde `@/features/payments/hooks/`
- [ ] No hace polling si `pedidoId === null`
- [ ] No hace polling si `status !== 'waiting_payment'` (ya resuelto o idle)
- [ ] Polling cada 30 segundos con `setInterval`
- [ ] Cleanup de interval al desmontar (previene memory leaks)
- [ ] Polling se detiene cuando `estado !== 'pending'` en la respuesta
- [ ] Al recibir `approved` → `paymentStore.setStatus('success')`
- [ ] Al recibir `rejected` | `cancelled` → `paymentStore.setStatus('error')`
- [ ] Retry exponencial en error de red: 3 intentos con delays 1s, 2s, 4s
- [ ] `PaymentStatusModal` muestra "Verificando pago..." mientras `isPolling === true`
- [ ] Tests vitest cubren: polling activo, detención por estado, cleanup, retry en error
- [ ] Coverage ≥ 40% en el hook

## No incluido en este change

- Modificación del backend (endpoint ya existe)
- Cambios en `usePaymentStatus` (hook one-shot separado)
- Nuevo componente `PaymentStatusModal` desde cero (integración en existente)
- Instalación de nuevas dependencias npm
