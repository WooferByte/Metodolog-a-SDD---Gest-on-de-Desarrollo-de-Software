# Design: frontend-payment-status-polling

## Resumen

Hook personalizado `usePaymentStatusPolling` basado en `useEffect` + `setInterval`
que implementa polling activo contra `GET /api/v1/pagos/{pedido_id}/status`,
con máquina de estados de polling interna, retry exponencial y cleanup garantizado.

---

## 1. Diseño del Hook

### Signatura pública

```typescript
/**
 * usePaymentStatusPolling
 *
 * Polls GET /api/v1/pagos/{pedidoId}/status every POLL_INTERVAL_MS.
 * Stops automatically when mp_status !== 'pending'.
 * Updates paymentStore.status on state change.
 * Retries on network errors (max 3, exponential backoff: 1s, 2s, 4s).
 *
 * @param pedidoId  - Order ID to poll. Pass null to disable polling.
 * @returns         - { isPolling, retryCount, lastError }
 */
export function usePaymentStatusPolling(pedidoId: number | null): PollingResult
```

### Tipo de retorno

```typescript
export interface PollingResult {
  /** true while the interval is active and status is still 'pending' */
  isPolling: boolean
  /** current retry attempt count (resets on success) */
  retryCount: number
  /** last error message if any, null otherwise */
  lastError: string | null
}
```

### Constantes

```typescript
const POLL_INTERVAL_MS = 30_000      // 30 segundos entre polls
const MAX_RETRIES = 3                // máximo de reintentos por error
const RETRY_DELAYS_MS = [1000, 2000, 4000] // backoff exponencial (1s, 2s, 4s)
```

---

## 2. Máquina de Estados del Polling

```
IDLE
  │ pedidoId !== null && status === 'waiting_payment'
  ▼
ACTIVE ──────────────────────────────────────────────────────┐
  │ setInterval cada 30s                                      │
  │ fetchPaymentStatus(pedidoId)                              │
  ├─→ response.estado === 'approved'                          │
  │     paymentStore.setStatus('success')                     │
  │     clearInterval → STOPPED                               │
  ├─→ response.estado === 'rejected' | 'cancelled' | otro     │
  │     paymentStore.setStatus('error')                       │
  │     clearInterval → STOPPED                               │
  ├─→ response.estado === 'pending'                           │
  │     continuar polling                                      │
  └─→ Error de red                                            │
        retryCount < MAX_RETRIES?                              │
          sí → esperar RETRY_DELAYS_MS[retryCount], reintentar │
          no → paymentStore.setError(message)                  │
               clearInterval → ERROR_STOPPED                  │

STOPPED / ERROR_STOPPED
  │ componente se desmonta
  ▼
CLEANUP (clearInterval garantizado vía useEffect return)
```

### Estados del `mp_status` del backend (`estado` en `PagoStatusResponse`)

| `estado` en respuesta | Acción del hook | `paymentStore.status` resultante |
|-----------------------|-----------------|----------------------------------|
| `"pending"`           | Continuar polling | `'waiting_payment'` (sin cambio) |
| `"approved"`          | Detener, éxito  | `'success'` |
| `"rejected"`          | Detener, error  | `'error'` |
| `"cancelled"`         | Detener, error  | `'error'` |
| cualquier otro        | Detener, error  | `'error'` (por seguridad) |

---

## 3. Implementación del Hook — Pseudocódigo

```typescript
export function usePaymentStatusPolling(pedidoId: number | null): PollingResult {
  const setStatus  = usePaymentStore((state) => state.setStatus)
  const setError   = usePaymentStore((state) => state.setError)
  const storeStatus = usePaymentStore((state) => state.status)

  const [isPolling, setIsPolling] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [lastError, setLastError] = useState<string | null>(null)

  // Usar ref para retryCount dentro de setInterval (evita stale closure)
  const retryCountRef = useRef(0)

  const shouldPoll = pedidoId !== null && storeStatus === 'waiting_payment'

  useEffect(() => {
    if (!shouldPoll) {
      setIsPolling(false)
      return
    }

    setIsPolling(true)
    retryCountRef.current = 0
    setRetryCount(0)
    setLastError(null)

    // Función de fetch con retry exponencial
    const poll = async () => {
      try {
        const { data } = await apiClient.get<PaymentStatusResponse>(
          `/api/v1/pagos/${pedidoId}/status`
        )

        retryCountRef.current = 0
        setRetryCount(0)
        setLastError(null)

        if (data.estado === 'approved') {
          setStatus('success')
          clearInterval(intervalId)
          setIsPolling(false)
        } else if (data.estado === 'rejected' || data.estado === 'cancelled') {
          setStatus('error')
          clearInterval(intervalId)
          setIsPolling(false)
        } else if (data.estado !== 'pending') {
          // Estado desconocido — detener por seguridad
          setStatus('error')
          setError(`Estado de pago desconocido: ${data.estado}`)
          clearInterval(intervalId)
          setIsPolling(false)
        }
        // 'pending' → no hacer nada, esperar próximo tick
      } catch (err) {
        const current = retryCountRef.current

        if (current < MAX_RETRIES) {
          retryCountRef.current = current + 1
          setRetryCount(current + 1)

          // Retry con delay exponencial
          await new Promise(resolve =>
            setTimeout(resolve, RETRY_DELAYS_MS[current] ?? RETRY_DELAYS_MS.at(-1))
          )
          poll() // reintentar (fuera del interval — no acumula)
        } else {
          const msg = err instanceof Error ? err.message : 'Error al verificar el pago'
          setLastError(msg)
          setError(msg)
          clearInterval(intervalId)
          setIsPolling(false)
        }
      }
    }

    // Primera ejecución inmediata al montar
    poll()

    // Luego polling periódico
    const intervalId = setInterval(poll, POLL_INTERVAL_MS)

    // Cleanup garantizado
    return () => {
      clearInterval(intervalId)
      setIsPolling(false)
    }
  }, [pedidoId, shouldPoll, setStatus, setError])

  return { isPolling, retryCount, lastError }
}
```

### Notas de implementación

**Stale closure con `retryCountRef`**: El `setInterval` captura la closure de la primera
ejecución de `useEffect`. Para acceder al valor actualizado de `retryCount` dentro del
callback del interval, se usa un `useRef` sincronizado con el estado.

**Primera llamada inmediata**: El hook llama a `poll()` una vez al montar antes de que
arranque el interval, así el usuario no espera 30 segundos para la primera verificación.

**`intervalId` antes de la primera llamada**: La variable `intervalId` se declara con `let`
antes del primer `poll()` para que el closure de `poll` capture la referencia correcta.

**Dependencias del `useEffect`**: `[pedidoId, shouldPoll, setStatus, setError]`.
`shouldPoll` es derivado de `storeStatus` — cambiar a `'waiting_payment'` dispara el effect.
Salir de `'waiting_payment'` (por otro componente) dispara el cleanup.

---

## 4. Integración en PaymentStatusModal

El modal existente consume el hook así:

```tsx
// En PaymentStatusModal (o donde se use)
const { isPolling, lastError } = usePaymentStatusPolling(pedidoId)

// Mientras polling activo:
{isPolling && (
  <div role="status" aria-live="polite" className="flex items-center gap-2">
    <Spinner className="size-4 animate-spin text-primary" />
    <span className="text-sm text-muted-foreground">Verificando pago...</span>
  </div>
)}
```

La UI se actualiza reactivamente cuando `paymentStore.status` cambia a `'success'`
o `'error'` — el modal puede condicionar su contenido en ese campo.

---

## 5. Consideraciones de Diseño

### Por qué `useEffect` + `setInterval` y no `refetchInterval` de TanStack Query

| Criterio | `setInterval` + `useEffect` | TanStack `refetchInterval` |
|----------|----------------------------|---------------------------|
| Parada por contenido de respuesta | Nativa — dentro del callback | Requiere `refetchIntervalInBackground` + `enabled` workaround |
| Retry exponencial custom | Total control | Solo `retryDelay` global, no por contexto de polling |
| Estado de polling visible | `useState` local | No hay flag nativo "estoy en polling" |
| Separación de responsabilidades | Estado proceso (cliente) → Zustand | Estado servidor → Query cache |
| Cleanup garantizado | `useEffect` return | `queryClient.cancelQueries()` |

La decisión es coherente con la arquitectura del proyecto: Zustand para estado cliente
(proceso de pago), TanStack Query para estado servidor (datos del producto, pedido).

### Por qué no duplicar `usePaymentStatus`

`usePaymentStatus` es un one-shot query para verificar el estado post-redirect (cuando MP
redirige al usuario de vuelta). `usePaymentStatusPolling` es un daemon de polling que corre
mientras el modal está visible. Son concerns distintos — mantenerlos separados permite
reutilizar `usePaymentStatus` en otros contextos sin acoplarlo al polling.

### Seguridad

- El hook no persiste ningún dato en localStorage.
- Si el componente se desmonta (usuario navega), el interval se limpia inmediatamente.
- En caso de error máximo, se setea `paymentStore.status = 'error'` para que la UI
  propague el error al usuario (no se silencia).

---

## 6. Tests

### Estrategia de testing (vitest + @testing-library/react)

```
frontend/src/features/payments/hooks/__tests__/
└── usePaymentStatusPolling.test.ts
```

| Test | Descripción |
|------|-------------|
| 1. No polling si `pedidoId === null` | `isPolling` debe ser `false` desde el inicio |
| 2. No polling si `status !== 'waiting_payment'` | Hook inactivo si store en `idle` |
| 3. Polling activo con `pedidoId` + `waiting_payment` | `isPolling === true` al montar |
| 4. Detención en `approved` | Llama a `setStatus('success')`, `isPolling = false` |
| 5. Detención en `rejected` | Llama a `setStatus('error')`, `isPolling = false` |
| 6. Detención en `cancelled` | Mismo que `rejected` |
| 7. Estado desconocido → error | `setStatus('error')` + `setError` |
| 8. Cleanup al desmontar | `clearInterval` llamado, no más llamadas a API |
| 9. Retry en error de red — 1er intento | `retryCount === 1` después de primer fallo |
| 10. Retry agotado (3 intentos) | `setError` llamado, `isPolling = false` |
| 11. `pending` continúa polling | Estado sin cambio, interval sigue activo |
| 12. Primera llamada inmediata al montar | API llamada antes de los 30s del interval |

### Patrón de mocking

```typescript
// Usar vi.useFakeTimers() para controlar setInterval
// Usar vi.mock('@/shared/api/axios') para mockear apiClient
// Usar renderHook de @testing-library/react
// Usar act() para avanzar timers
```

---

## 7. Archivos Afectados

```
frontend/src/features/payments/hooks/
├── usePaymentStatusPolling.ts          ← CREAR
└── __tests__/
    └── usePaymentStatusPolling.test.ts ← CREAR
```

Sin cambios en backend, store, tipos existentes (todos son compatibles).
`PaymentStatusResponse.estado` ya existe en `payment.types.ts` como `string`.
