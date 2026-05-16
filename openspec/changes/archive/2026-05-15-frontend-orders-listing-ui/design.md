## Context

El backend de pedidos está completamente operativo (archivado en `orders-fsm-backend` y `orders-api-endpoints`). El endpoint `GET /api/v1/pedidos` responde con paginación `{ items, total, limit, offset }`. Cada pedido incluye: `id`, `usuario_id`, `estado_pedido_id` (1–6), `total`, `creado_en`, `observacion`, `direccion_snapshot`, `forma_pago_id`.

El frontend actualmente tiene implementado el feature `products` como único feature bajo FSD. No existe ninguna UI para pedidos. Los roles ADMIN (1), STOCK (2), PEDIDOS (3) y CLIENT (4) están definidos en el sistema RBAC con IDs estables.

**Restricciones duras del stack:**
- Tailwind v4 — solo tokens semánticos `@theme`, sin clases hardcodeadas
- TanStack Query v5 — servidor state únicamente
- Zustand v5 — cliente state únicamente (filtros UI), nunca duplicar datos del servidor
- `React.lazy` + `Suspense` — obligatorio en ambas páginas nuevas
- Vitest (no jest), `__tests__/` por capa
- Path alias `@/` en todos los imports

## Goals / Non-Goals

**Goals:**
- Pantalla `/mis-pedidos` para CLIENT con timeline visual de pedidos propios (paginación, skeleton, estado vacío).
- Panel `/admin/pedidos` para ADMIN/PEDIDOS con tabla profesional, filtros y paginación.
- Componente `OrderCard` compartido entre ambas vistas con prop `mode: "client" | "admin"`.
- Badge semántico de estado (`OrderStatusBadge`) mapeando IDs 1–6 a colores `@theme`.
- Tests vitest cubriendo `OrderCard`, skeletons, estados vacíos.
- Tests E2E Playwright cubriendo flujos por rol, filtrado y paginación.
- ARIA completo: `role="table"`, `aria-label` en filtros, `aria-current` en paginación.
- Responsive mobile-first desde el primer componente.

**Non-Goals:**
- Detalle individual de pedido (`/mis-pedidos/:id`) — es otro change posterior.
- Acción de cambio de estado en el panel admin — ese flujo involucra la FSM del backend y se maneja en un change separado.
- Vista de pedidos en tiempo real (WebSocket/SSE) — fuera de scope.
- Crear o cancelar pedidos desde estas pantallas.

## Decisions

### D1: Separación estricta estado servidor vs. cliente

**Decisión:** TanStack Query gestiona exclusivamente los datos de pedidos (server state). Zustand gestiona exclusivamente los filtros de UI del panel admin (estado seleccionado, fecha, búsqueda por usuario).

**Alternativa descartada:** Usar un único Zustand store para todo. Descartada porque violaría la regla mandatoria del proyecto (`❌ NUNCA duplicar datos del servidor en Zustand`) y perdería el cache/invalidation automático de TanStack Query.

**Consecuencia:** `useOrders.ts` usa `useQuery` con `placeholderData: keepPreviousData` para evitar flash en paginación. Los filtros se leen del Zustand store al componer los query params.

### D2: Componente OrderCard compartido con prop `mode`

**Decisión:** Un único componente `OrderCard` acepta `mode: "client" | "admin"` para renderizar variantes visuales distintas (timeline card vs. fila de tabla compacta).

**Alternativa descartada:** Dos componentes separados `OrderCardClient` y `OrderCardAdmin`. Descartada por duplicación de lógica de badge y formateo de fechas/totales.

**Consecuencia:** Props de OrderCard incluyen `order: Order`, `mode: "client" | "admin"`, y opciones de acción (CTA detalle para client, acciones admin).

### D3: Estados de pedido como constante tipada — NO como enum TS

**Decisión:** Mapeo de ID a metadata (label, color token) declarado como `const ORDER_STATUS_MAP` de tipo `Record<number, OrderStatusMeta>` en `features/orders/constants/`.

**Alternativa descartada:** Enum TypeScript. Descartado porque los IDs vienen del backend como números; el enum TS no se serializa directo desde JSON y requeriría casting extra.

**Consecuencia:** `OrderStatusBadge` recibe `statusId: number` y consulta el mapa para obtener label y clase de color semántico.

**Tokens de color por estado (Tailwind v4 `@theme`):**
| ID | Estado | Color token |
|----|--------|-------------|
| 1 | PENDIENTE | `--color-warning` (amarillo) |
| 2 | CONFIRMADO | `--color-info` (azul) |
| 3 | EN_PREPARACIÓN | `--color-accent-orange` (naranja) |
| 4 | EN_CAMINO | `--color-accent-purple` (púrpura) |
| 5 | ENTREGADO | `--color-success` (verde) |
| 6 | CANCELADO | `--color-muted-foreground` (gris) |

Si los tokens `--color-warning`, `--color-success`, etc. aún no existen en el `@theme` global, el implementador debe agregarlos al CSS base durante este change.

### D4: Filtros admin en Zustand store — NO en URL params

**Decisión:** Los filtros (estado seleccionado, rango de fecha, término de búsqueda) se almacenan en un store Zustand `useOrdersFilterStore`.

**Alternativa descartada:** URL search params (`useSearchParams`). Descartada porque la pantalla admin no necesita URLs compartibles para los filtros, y añade complejidad de sincronización bidireccional.

**Consecuencia:** Al desmontar `OrdersPanelPage` los filtros persisten en memoria (sin `persist` middleware). Reset explícito en el botón "Limpiar filtros".

### D5: Skeletons específicos — NO spinners genéricos

**Decisión:** `OrdersSkeleton` renderiza la forma exacta del contenido que va a aparecer: tarjetas de tamaño aproximado en modo client, filas de tabla en modo admin.

**Alternativa descartada:** Spinner centrado o `loading...` text. Descartado porque produce CLS y UX inferior.

### D6: React.lazy + Suspense en el router principal

**Decisión:** Ambas páginas se cargan con `React.lazy`. El `Suspense` wrapper usa el componente de skeleton correspondiente como `fallback` (no un spinner genérico).

**Consecuencia:** El router debe importar las páginas con `const MyOrdersPage = React.lazy(() => import('@/pages/MyOrdersPage'))`.

### D7: Tabla admin — HTML semántico con ARIA explícito

**Decisión:** `OrdersTable` usa `<table>` nativo con `role="table"`, `<thead>`, `<tbody>`, `<th scope="col">`, `<td>`. No usar div-grid para tablas de datos.

**Alternativa descartada:** `div` grid con `role="grid"`. Descartado porque `<table>` nativa con `scope` es más accesible para screen readers con datos tabulares relacionales.

## Risks / Trade-offs

- **[Riesgo] Tokens semánticos de color no definidos en `@theme`** → Mitigación: task explícita en tasks.md para verificar/agregar tokens antes de implementar `OrderStatusBadge`.
- **[Riesgo] El endpoint `GET /api/v1/pedidos` filtra por `usuario_id` del token JWT en backend (CLIENT solo ve sus pedidos)** → Verificar en task de integración que la lógica de filtrado ya esté en el backend y no sea necesario pasar `usuario_id` como query param.
- **[Riesgo] Paginación con `keepPreviousData` puede mostrar datos stale si el offset cambia rápido** → Aceptable para este MVP; agregar `isFetching` indicator sutil en la UI.
- **[Trade-off] Filtros en Zustand vs URL params**: Se pierde compartibilidad de URLs filtradas, a cambio de menor complejidad. Aceptable para panel interno ADMIN/PEDIDOS.
- **[Riesgo] Playwright requiere backend real corriendo** → Los tests E2E mockean el backend con `page.route` siguiendo el patrón de la skill `testing-e2e-playwright`.

## Migration Plan

No hay migración de datos. Despliegue incremental:
1. Implementar feature layer (`types`, `hooks`, `components`) — no rompe nada existente.
2. Crear páginas y registrar rutas bajo guards existentes.
3. Ejecutar `vitest run` + `playwright test` antes de archivar.
4. El router principal se actualiza en el mismo PR/commit que las páginas.

**Rollback**: eliminar las rutas del router + las carpetas de features creadas. Sin impacto en backend ni base de datos.

## Open Questions

- **OQ-1**: ¿El endpoint `GET /api/v1/pedidos` ya filtra automáticamente por `usuario_id` cuando el token es de rol CLIENT, o necesita el query param `usuario_id=<id>`? → Verificar antes de implementar `useOrders`.
- **OQ-2**: ¿El panel admin debe soportar cambio de estado de pedido en esta misma pantalla (inline), o solo "ver detalle"? → Según task context: solo ver detalle en este change. Cambio de estado en change posterior.
- **OQ-3**: ¿Los tokens de color semánticos extra (`--color-warning`, `--color-success`, `--color-info`, `--color-accent-orange`, `--color-accent-purple`) ya existen en el `@theme` global del proyecto? → Verificar en `frontend/src/app/globals.css` o equivalente antes de implementar `OrderStatusBadge`.
