## Context

**Estado actual**: El frontend tiene un Error Boundary básico (`src/app/ErrorBoundary.tsx`) con estilos inline (no Tailwind), un interceptor Axios (`src/shared/api/axios.ts`) que maneja refresh de 401 pero no mapea ningún otro status code a mensajes legibles, y un `useUIStore` con `addToast`/`removeToast` ya implementados pero sin consumidor visual (no existe `ToastContainer`).

**Contrato backend**: El backend ya devuelve RFC 7807 en todos los errores HTTP:
```json
{ "type": "...", "title": "...", "status": 400, "detail": "...", "instance": "..." }
```

**Restricciones**:
- React 18 — Error Boundary es la única razón para usar class component (no hay hooks para renderizado).
- Zustand v5 — `useUIStore` ya existe con `addToast(toast: Omit<Toast, 'id'>)`.
- Tailwind v4 — CSS-first, sin `tailwind.config.ts`, usar `@theme` tokens.
- Sin nuevas dependencias de terceros.

---

## Goals / Non-Goals

**Goals:**
- Error Boundary con visual Tailwind v4 coherente con el design system
- Interceptor Axios que mapea status codes HTTP a mensajes en español y despacha toasts
- Componente `ToastContainer` que renderiza el slice de `uiStore.toasts` con auto-dismiss
- Tipo `ApiError` tipado para RFC 7807
- Tests vitest ≥ 40% cobertura en los módulos nuevos

**Non-Goals:**
- Sistema de logging remoto (Sentry, Datadog) — fuera de alcance
- Manejo de errores de formularios (validación client-side) — ese es responsabilidad de TanStack Form cuando llegue
- Retry automático de requests fallidos (excepto el refresh 401 ya implementado)
- Toast persistente o con acción (ej. "Ver detalle") — versión MVP, solo mensaje + tipo

---

## Decisions

### D-1: Error Boundary no usa hooks — sigue siendo class component

**Decisión**: Mantener como class component. No migrar a ningún wrapper de librería.

**Alternativas consideradas**:
- `react-error-boundary` lib: evitada — agrega dependencia innecesaria; la implementación manual es simple y controlable.
- Function component con `useErrorBoundary` hook: no existe en React 18 estable.

**Rationale**: React 18 requiere class component para `getDerivedStateFromError` + `componentDidCatch`. El componente es simple y estable; no justifica dependencia externa.

### D-2: El interceptor Axios reutiliza la instancia singleton existente — no crea nueva

**Decisión**: Ampliar el bloque `apiClient.interceptors.response.use` existente. El tramo de error actual retorna `Promise.reject(error)` para status ≠ 401; interceptar ese reject antes de propagarlo para mapear status codes y disparar toast.

**Alternativas consideradas**:
- Agregar interceptor separado (segundo `.use()`): técnicamente válido, pero crea dos interceptores en la misma instancia y el orden de ejecución depende del registro — más frágil.
- Manejar errores en cada hook TanStack Query: duplica la lógica en N lugares.

**Rationale**: Un único punto centralizado; el mapeo de errores HTTP es transversal y no debe dispersarse en hooks de feature.

### D-3: Toast state vive en Zustand uiStore — no en Context React

**Decisión**: Usar `useUIStore.addToast` / `removeToast` desde el interceptor Axios (acceso directo via `.getState()`) y desde el componente `ToastContainer` (via selector hook).

**Alternativas consideradas**:
- Context API propio: más boilerplate, y uiStore ya existe y ya tiene el slice de toasts con los tipos correctos.
- Estado local en `ToastContainer` con `EventEmitter`: patrón válido para frameworks sin store, innecesario aquí.

**Rationale**: uiStore ya está diseñado para este caso de uso. Zustand permite acceso fuera de React (`.getState()`) sin violar hooks rules, lo que es necesario para el interceptor.

### D-4: Mapeo de status codes — mensajes fijos en español, priorizando `detail` RFC 7807

**Decisión**: El interceptor lee `error.response.data.detail` (RFC 7807) si existe; si no, usa mensajes fallback por status code:

| Status | Toast type | Mensaje fallback |
|--------|-----------|-----------------|
| 400 | warning | "Datos inválidos. Revisá los campos." |
| 403 | error | "No tenés permiso para esta acción." |
| 404 | info | "El recurso solicitado no existe." |
| 422 | warning | "Error de validación en los datos enviados." |
| 429 | warning | "Demasiadas solicitudes. Esperá un momento." |
| 500 | error | "Error del servidor. Intentá más tarde." |
| otros | error | "Ocurrió un error inesperado." |

**Rationale**: RFC 7807 `detail` es más preciso y contextual; el fallback asegura UX decente sin depender de que el backend siempre lo incluya.

### D-5: Auto-dismiss configurable con duración por tipo

**Decisión**: `ToastContainer` inicia un `setTimeout` al montar cada toast. Duración defaults:
- `success`, `info`: 4000ms
- `warning`: 5000ms
- `error`: 6000ms (errores meriten más tiempo de lectura)

El `duration` del toast tiene precedencia si está definido.

**Rationale**: Los errores son críticos — darle al usuario tiempo suficiente para leer el mensaje antes de desaparecer.

### D-6: Ubicación en FSD

| Artefacto | Path | Layer |
|-----------|------|-------|
| `ErrorBoundary.tsx` | `src/app/ErrorBoundary.tsx` | app |
| `axios.ts` (modificado) | `src/shared/api/axios.ts` | shared/api |
| `ToastContainer.tsx` | `src/shared/components/ToastContainer.tsx` | shared/components |
| `api.ts` (tipos) | `src/shared/types/api.ts` | shared |

**Rationale**: FSD coloca infraestructura HTTP en `shared/api`, componentes compartidos en `shared/components`, tipos globales en `shared/types`. `ErrorBoundary` en `app` porque envuelve el árbol completo.

---

## Risks / Trade-offs

- **[Riesgo] El interceptor ejecuta `useUIStore.getState()` fuera de React** → Mitigación: Zustand v5 permite esto por diseño (`.getState()` es síncrono y no viola hooks rules). Ya existe este patrón en `axios.ts` para `useAuthStore.getState().accessToken`.

- **[Riesgo] El Error Boundary no captura errores en event handlers ni async** → Mitigación: documentado en comentario del componente; para esos casos el toast del interceptor Axios ya provee feedback. No hay coverage gap significativo.

- **[Riesgo] Toasts acumulados si múltiples requests fallan simultáneamente** → Mitigación: limitar cola de toasts a máximo 5 activos simultáneos en `addToast` — descartar el más antiguo si se supera el límite.

- **[Trade-off] Sin animación de entrada/salida CSS** → Aceptado para MVP; Tailwind v4 `@keyframes` pueden agregarse en un change de layout posterior sin cambiar la API del componente.

---

## Migration Plan

1. Crear `src/shared/types/api.ts` con el tipo `ApiError`
2. Modificar `src/app/ErrorBoundary.tsx` — reemplazar estilos inline con Tailwind v4
3. Crear `src/shared/components/ToastContainer.tsx`
4. Modificar `src/shared/api/axios.ts` — extender interceptor de error
5. Modificar `src/app/App.tsx` — agregar `<ToastContainer />` dentro del árbol
6. Escribir tests en `__tests__/`
7. `npx vitest run` — verificar ≥ 40% cobertura en módulos nuevos/modificados

**Rollback**: los cambios son aditivos (nuevo componente, extensión de interceptor). Revertir `App.tsx` + `axios.ts` deshace visibilidad de toasts sin afectar auth flow.

---

## Open Questions

- ¿El Error Boundary debe tener botón "Ir al inicio" además de "Recargar"? → Aceptado: sí, agregar link a `/` para UX más completa.
- ¿Los toasts de error deben tener botón de cierre manual o solo auto-dismiss? → Decisión: ambos — auto-dismiss Y botón X para cerrar.
