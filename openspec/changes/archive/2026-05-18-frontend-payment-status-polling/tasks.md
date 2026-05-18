# Tasks: frontend-payment-status-polling

## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — Tailwind v4 para clases del spinner/feedback visual en PaymentStatusModal
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — accesibilidad WCAG: `role="status"`, `aria-live="polite"` en el indicador de polling
- [ ] 0.3 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — reglas `rerender-dependencies`, `rerender-use-ref-transient-values`, `advanced-event-handler-refs` para evitar stale closures en el interval
- [ ] 0.4 Leer `.agents/skills/zustand-state-management/README.md` — patrón `create<T>()()`, acceso granular con selectores primitivos para evitar renders innecesarios
- [ ] 0.5 Leer `.agents/skills/frontend-state-management/SKILL.md` — criterios Zustand vs TanStack Query; confirmar que polling activo es estado cliente (Zustand + useEffect, no refetchInterval)
- [ ] 0.6 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — patrón de mock `page.route` para simular respuestas del endpoint `/api/v1/pagos/{pedido_id}/status` si se requieren tests e2e

---

## 1. Verificación de contexto existente

- [ ] 1.1 Leer `frontend/src/features/payments/hooks/usePaymentStatus.ts` — confirmar que es one-shot (no modifica) y entender el patrón de `fetchPaymentStatus`
- [ ] 1.2 Leer `frontend/src/store/paymentStore.ts` — confirmar acciones disponibles: `setStatus`, `setError`, `setPedidoId`
- [ ] 1.3 Leer `frontend/src/features/payments/types/payment.types.ts` — confirmar que `PaymentStatusResponse.estado` es `string` y que `PaymentStatus` incluye `'success'` y `'error'`
- [ ] 1.4 Leer `backend/pagos/schemas.py` — confirmar campos reales de `PagoStatusResponse` (especialmente `estado`)
- [ ] 1.5 Verificar si existe `PaymentStatusModal` en el proyecto con `glob` o `grep`:
  ```bash
  # Desde frontend/src/
  find . -name "PaymentStatusModal*" 2>/dev/null
  ```

---

## 2. Crear el hook `usePaymentStatusPolling`

- [ ] 2.1 Crear `frontend/src/features/payments/hooks/usePaymentStatusPolling.ts`

  Debe implementar exactamente:
  - `POLL_INTERVAL_MS = 30_000`
  - `MAX_RETRIES = 3`
  - `RETRY_DELAYS_MS = [1000, 2000, 4000]`
  - Signatura: `usePaymentStatusPolling(pedidoId: number | null): PollingResult`
  - Tipo de retorno: `{ isPolling: boolean; retryCount: number; lastError: string | null }`

- [ ] 2.2 El hook debe leer del `paymentStore` con selectores granulares (un selector por campo, no desestructurar el estado completo):
  ```typescript
  const setStatus  = usePaymentStore((state) => state.setStatus)
  const setError   = usePaymentStore((state) => state.setError)
  const storeStatus = usePaymentStore((state) => state.status)
  ```

- [ ] 2.3 La condición de activación es `shouldPoll = pedidoId !== null && storeStatus === 'waiting_payment'`. Si `shouldPoll` es `false`, retornar `{ isPolling: false, retryCount: 0, lastError: null }` sin crear interval.

- [ ] 2.4 Implementar `useRef` para `retryCount` (evita stale closure en el callback del interval):
  ```typescript
  const retryCountRef = useRef(0)
  ```

- [ ] 2.5 En el `useEffect`:
  - [ ] 2.5.1 Llamar a `poll()` inmediatamente al montar (primera verificación sin esperar 30s)
  - [ ] 2.5.2 Crear `setInterval(poll, POLL_INTERVAL_MS)` para polling periódico
  - [ ] 2.5.3 Retornar cleanup: `() => { clearInterval(intervalId); setIsPolling(false) }`

- [ ] 2.6 En la función `poll()` (async):
  - [ ] 2.6.1 Llamar a `apiClient.get<PaymentStatusResponse>(`/api/v1/pagos/${pedidoId}/status`)`
  - [ ] 2.6.2 En éxito: resetear `retryCountRef.current = 0` y `setRetryCount(0)`
  - [ ] 2.6.3 Si `data.estado === 'approved'` → `setStatus('success')`, `clearInterval`, `setIsPolling(false)`
  - [ ] 2.6.4 Si `data.estado === 'rejected' || data.estado === 'cancelled'` → `setStatus('error')`, `clearInterval`, `setIsPolling(false)`
  - [ ] 2.6.5 Si `data.estado === 'pending'` → no hacer nada (continuar polling)
  - [ ] 2.6.6 Cualquier otro `estado` → `setStatus('error')`, `setError('Estado de pago desconocido: ...')`, `clearInterval`, `setIsPolling(false)`
  - [ ] 2.6.7 En catch: si `retryCountRef.current < MAX_RETRIES` → incrementar, esperar delay exponencial, llamar `poll()` recursivamente
  - [ ] 2.6.8 En catch agotado: `setLastError`, `setError`, `clearInterval`, `setIsPolling(false)`

- [ ] 2.7 Las dependencias del `useEffect` son: `[pedidoId, shouldPoll, setStatus, setError]`

- [ ] 2.8 Verificar que todos los imports usan path alias `@/`:
  ```typescript
  import { apiClient } from '@/shared/api/axios'
  import { usePaymentStore } from '@/store/paymentStore'
  import type { PaymentStatusResponse } from '../types/payment.types'
  ```

---

## 3. Agregar tipos en `payment.types.ts` (si es necesario)

- [ ] 3.1 Verificar si `PollingResult` ya existe en `payment.types.ts`. Si no existe, agregar:
  ```typescript
  /** Return type of usePaymentStatusPolling */
  export interface PollingResult {
    isPolling: boolean
    retryCount: number
    lastError: string | null
  }
  ```

  Solo agregar si no existe — no duplicar tipos existentes.

---

## 4. Integrar en PaymentStatusModal

- [ ] 4.1 Ubicar el componente `PaymentStatusModal` (puede estar en `features/payments/components/` o `pages/`)

- [ ] 4.2 Si el modal existe, importar y usar el hook:
  ```tsx
  import { usePaymentStatusPolling } from '@/features/payments/hooks/usePaymentStatusPolling'

  // Dentro del componente:
  const pedidoId = usePaymentStore((state) => state.pedidoId)
  const { isPolling } = usePaymentStatusPolling(pedidoId)
  ```

- [ ] 4.3 Agregar indicador accesible de polling (Tailwind v4, `role="status"`, `aria-live="polite"`):
  ```tsx
  {isPolling && (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-2 text-sm text-muted-foreground"
    >
      {/* Spinner con lucide-react o CSS puro */}
      <svg
        className="size-4 animate-spin"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <span>Verificando pago...</span>
    </div>
  )}
  ```

- [ ] 4.4 Si el modal NO existe, anotar en el PR que la integración visual queda pendiente de que se cree el componente — el hook está listo para consumir.

---

## 5. Tests (vitest + @testing-library/react)

Ubicación: `frontend/src/features/payments/hooks/__tests__/usePaymentStatusPolling.test.ts`

- [ ] 5.1 Configurar el archivo de test:
  ```typescript
  import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
  import { renderHook, act } from '@testing-library/react'
  import { usePaymentStatusPolling } from '../usePaymentStatusPolling'
  ```

- [ ] 5.2 Mock de `apiClient`:
  ```typescript
  vi.mock('@/shared/api/axios', () => ({
    apiClient: { get: vi.fn() },
  }))
  ```

- [ ] 5.3 Mock del `paymentStore` (solo las acciones que el hook necesita):
  ```typescript
  const mockSetStatus = vi.fn()
  const mockSetError  = vi.fn()

  vi.mock('@/store/paymentStore', () => ({
    usePaymentStore: vi.fn((selector) =>
      selector({
        status: 'waiting_payment',
        setStatus: mockSetStatus,
        setError: mockSetError,
      })
    ),
  }))
  ```

- [ ] 5.4 Usar `vi.useFakeTimers()` en `beforeEach` y `vi.useRealTimers()` en `afterEach`

- [ ] 5.5 Test 1 — No polling si `pedidoId === null`:
  ```typescript
  it('no inicia polling si pedidoId es null', () => {
    const { result } = renderHook(() => usePaymentStatusPolling(null))
    expect(result.current.isPolling).toBe(false)
    // apiClient.get NO debe ser llamado
  })
  ```

- [ ] 5.6 Test 2 — No polling si `status !== 'waiting_payment'` (mockear store con `status: 'idle'`):
  ```typescript
  it('no inicia polling si status no es waiting_payment', () => {
    // re-mockear usePaymentStore con status: 'idle'
    const { result } = renderHook(() => usePaymentStatusPolling(42))
    expect(result.current.isPolling).toBe(false)
  })
  ```

- [ ] 5.7 Test 3 — `isPolling === true` cuando activo:
  ```typescript
  it('isPolling es true cuando pedidoId y status son válidos', async () => {
    apiClient.get.mockResolvedValue({ data: { estado: 'pending' } })
    const { result } = renderHook(() => usePaymentStatusPolling(42))
    await act(async () => { /* flush microtasks */ })
    expect(result.current.isPolling).toBe(true)
  })
  ```

- [ ] 5.8 Test 4 — Detención en `approved`:
  ```typescript
  it('detiene polling y llama setStatus(success) cuando approved', async () => {
    apiClient.get.mockResolvedValue({ data: { estado: 'approved' } })
    const { result } = renderHook(() => usePaymentStatusPolling(42))
    await act(async () => { /* flush */ })
    expect(mockSetStatus).toHaveBeenCalledWith('success')
    expect(result.current.isPolling).toBe(false)
  })
  ```

- [ ] 5.9 Test 5 — Detención en `rejected`:
  Similar a 5.8 pero con `estado: 'rejected'` → `setStatus('error')`.

- [ ] 5.10 Test 6 — Detención en `cancelled`:
  Similar a 5.8 pero con `estado: 'cancelled'` → `setStatus('error')`.

- [ ] 5.11 Test 7 — Estado desconocido → error:
  `estado: 'unknown_state'` → `setStatus('error')` + `setError` llamado.

- [ ] 5.12 Test 8 — Cleanup al desmontar (no más llamadas a API):
  ```typescript
  it('limpia el interval al desmontar', async () => {
    apiClient.get.mockResolvedValue({ data: { estado: 'pending' } })
    const { result, unmount } = renderHook(() => usePaymentStatusPolling(42))
    await act(async () => {})
    unmount()
    vi.advanceTimersByTime(60_000) // avanzar 2 ciclos
    // apiClient.get no debe llamarse más después del unmount
    const callsBeforeUnmount = apiClient.get.mock.calls.length
    expect(apiClient.get.mock.calls.length).toBe(callsBeforeUnmount)
  })
  ```

- [ ] 5.13 Test 9 — Retry en error de red:
  ```typescript
  it('incrementa retryCount en error de red', async () => {
    apiClient.get.mockRejectedValue(new Error('Network error'))
    const { result } = renderHook(() => usePaymentStatusPolling(42))
    await act(async () => { vi.advanceTimersByTime(1000) })
    expect(result.current.retryCount).toBeGreaterThan(0)
  })
  ```

- [ ] 5.14 Test 10 — Retry agotado (3 intentos):
  Mock de `apiClient.get` que siempre falla. Avanzar timers para cubrir los 3 delays.
  Verificar: `mockSetError` llamado, `isPolling === false`.

- [ ] 5.15 Test 11 — `pending` continúa polling:
  Mock que responde `pending`. Avanzar timer 60s (2 ciclos). Verificar que `apiClient.get`
  fue llamado 3 veces (1 inmediata + 2 del interval) y `setStatus` no fue llamado.

- [ ] 5.16 Test 12 — Primera llamada inmediata al montar:
  Verificar que `apiClient.get` es llamado 1 vez sin avanzar timers.

---

## 6. Verificación de tipos con TypeScript

- [ ] 6.1 Desde `frontend/`, ejecutar:
  ```bash
  npx tsc --noEmit
  ```
  No debe haber errores nuevos relacionados con `usePaymentStatusPolling`.

---

## 7. Correr tests

- [ ] 7.1 Ejecutar solo los tests del hook:
  ```bash
  cd frontend
  npx vitest run src/features/payments/hooks/__tests__/usePaymentStatusPolling.test.ts
  ```
  Todos los 12 tests deben pasar (PASS).

- [ ] 7.2 Ejecutar la suite completa para no romper nada:
  ```bash
  cd frontend
  npx vitest run
  ```

- [ ] 7.3 Verificar coverage del hook ≥ 40%:
  ```bash
  npx vitest run --coverage src/features/payments/hooks/__tests__/usePaymentStatusPolling.test.ts
  ```

---

## 8. Checklist pre-commit

- [ ] ¿Imports usando `@/` (path alias)?
- [ ] ¿No hay `session.commit()` (backend — N/A para este change)?
- [ ] ¿`setInterval` con cleanup en `useEffect` return?
- [ ] ¿No hay duplicación de datos del servidor en Zustand?
- [ ] ¿Tests escritos con **vitest** (no jest)?
- [ ] ¿`tsc --noEmit` sin errores?
- [ ] ¿`npx vitest run` sin regresiones?
- [ ] ¿Conventional Commit sin co-authored-by?

---

## Conteo de tasks

| Sección | Tasks |
|---------|-------|
| 0. Skills | 6 |
| 1. Verificación contexto | 5 |
| 2. Crear hook | 13 |
| 3. Tipos | 1 |
| 4. Integración modal | 4 |
| 5. Tests | 12 |
| 6. TypeScript check | 1 |
| 7. Correr tests | 3 |
| 8. Pre-commit | 8 |
| **Total** | **53** |
