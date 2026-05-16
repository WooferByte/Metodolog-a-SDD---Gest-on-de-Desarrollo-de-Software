## Context

El backend de pedidos está completamente operativo (archivado en `orders-fsm-backend` y `orders-api-endpoints`). Los endpoints relevantes para este change son:

- `GET /api/v1/pedidos/{id}` → retorna `PedidoDetailResponse` con `detalles[]` (snapshots) e `historial[]`.
- `DELETE /api/v1/pedidos/{id}` → cancela el pedido, revierte stock, soft-delete.
- `PATCH /api/v1/pedidos/{id}/estado` → avanza el estado FSM (solo ADMIN/PEDIDOS).

El frontend tiene operativo el listado (`/mis-pedidos` y `/admin/pedidos`) con `OrderCard`, `OrderStatusBadge`, `OrdersTable`, `useOrders` y el store de filtros Zustand. Los tipos base `Order` y `DireccionSnapshot` existen en `features/orders/types/index.ts`.

**Restricciones duras del stack (idénticas al change anterior):**
- Tailwind v4 — solo tokens semánticos `@theme`, sin colores hardcodeados.
- TanStack Query v5 — server state exclusivamente (datos del pedido, historial, detalles).
- Zustand v5 — cliente state exclusivamente (modal open/close del CancelOrderModal; NO duplicar datos del servidor).
- `React.lazy` + `Suspense` — obligatorio en las dos rutas nuevas.
- Vitest (no jest) con `@testing-library/react`, tests en `__tests__/` por capa.
- Path alias `@/` en todos los imports.
- Iconos con `lucide-react`.

**FSM recordatorio** (del spec `orders-fsm`):
| ID | Estado | Cancelable por CLIENT | Avanzable por ADMIN/PEDIDOS |
|----|--------|-----------------------|------------------------------|
| 1 | PENDIENTE | ✅ | → CONFIRMADO (solo sistema/webhook) |
| 2 | CONFIRMADO | ✅ (solo ADMIN) | → EN_PREPARACIÓN |
| 3 | EN_PREPARACIÓN | ❌ | → EN_CAMINO |
| 4 | EN_CAMINO | ❌ | → ENTREGADO |
| 5 | ENTREGADO | ❌ (terminal) | — |
| 6 | CANCELADO | ❌ (terminal) | — |

## Goals / Non-Goals

**Goals:**
- Página de detalle de pedido en `/pedidos/:id` para CLIENT (ownership check automático en backend).
- Página de detalle de pedido en `/admin/pedidos/:id` para ADMIN/PEDIDOS (acceso a cualquier pedido).
- Snapshot de productos congelados al momento de compra (NO datos live del producto).
- Timeline visual del historial FSM con animación de entrada y timestamp + usuario responsable.
- Botón "Cancelar" visible y habilitado solo cuando: rol CLIENT + estado PENDIENTE.
- Selector de estado visible y habilitado solo cuando: rol ADMIN o PEDIDOS + estado no terminal.
- CancelOrderModal con ARIA completo (dialog, focus trap, aria-labelledby, aria-describedby).
- Tests vitest cubriendo snapshot, timeline, modal.
- Tests E2E Playwright cubriendo acceso por rol, ver detalle, cancelar con confirmación.

**Non-Goals:**
- Edición de datos del pedido (no existe endpoint para ello).
- Vista de pedido en tiempo real (sin WebSocket/SSE en este change).
- Historial de pagos MercadoPago — ese flujo pertenece al change de pagos.
- Creación de pedidos desde la página de detalle.
- Modificar la dirección de entrega después de confirmar el pedido.

## Decisions

### D1: Un hook por operación — `useOrderDetail`, `useCancelOrder`, `useAdvanceOrderState`

**Decisión:** Tres hooks independientes siguiendo el patrón del change anterior (`useOrders`):
- `useOrderDetail(id: number)` → `useQuery` sobre `GET /api/v1/pedidos/{id}`.
- `useCancelOrder()` → `useMutation` sobre `DELETE /api/v1/pedidos/{id}`.
- `useAdvanceOrderState()` → `useMutation` sobre `PATCH /api/v1/pedidos/{id}/estado`.

**Alternativa descartada:** Un solo hook `useOrderActions` con todas las mutaciones. Descartada porque mezcla responsabilidades y complejiza el tree-shaking; además, `useAdvanceOrderState` solo se importa en la variante admin, y no debe aumentar el bundle de la página CLIENT.

**Consecuencia:** `OrderDetailPage` (CLIENT) importa `useOrderDetail` + `useCancelOrder`. La página admin importa adicionalmente `useAdvanceOrderState`. Los cambios exitosos invalidan `['orders']` y `['order-detail', id]` via `queryClient.invalidateQueries`.

### D2: Tipos extendidos — `OrderDetail` y `OrderHistorialItem`

**Decisión:** Extender los tipos existentes en `features/orders/types/index.ts`:

```ts
/** Detalle de línea del pedido — snapshot congelado al momento de compra */
export interface OrderDetailItem {
  id: number
  producto_id: number
  nombre_snapshot: string      // nombre del producto al momento de compra
  cantidad: number
  precio_snapshot: number      // precio por unidad al momento de compra
  personalizacion: number[]    // INTEGER[] (IDs de ingredientes modificados)
}

/** Entrada del historial FSM */
export interface OrderHistorialItem {
  id: number
  estado_anterior_id: number | null
  estado_nuevo_id: number
  usuario_responsable_id: number
  usuario_email: string | null // incluido por conveniencia si el backend lo expone
  creado_en: string            // ISO 8601
}

/** Detalle completo del pedido — respuesta de GET /api/v1/pedidos/{id} */
export interface OrderDetail extends Order {
  detalles: OrderDetailItem[]
  historial: OrderHistorialItem[]
}
```

**Alternativa descartada:** Crear un archivo de tipos separado `orderDetail.ts`. Descartada para mantener cohesión — los tipos del feature orders están centralizados en `types/index.ts` siguiendo el patrón del change anterior.

### D3: CancelOrderModal — estado UI en Zustand `useOrderDetailStore`, NO en useState local

**Decisión:** El estado de apertura del modal (`isCancelModalOpen: boolean`) se gestiona en un pequeño store Zustand `useOrderDetailStore` en `features/orders/store/orderDetailStore.ts`.

**Alternativa descartada:** `useState` local en el componente padre. Descartada porque si la implementación posterior necesita abrir el modal desde otro componente (ej: desde la barra de navegación en móvil), el estado local no escala. Con Zustand el costo es mínimo y la flexibilidad es mayor.

**Regla crítica:** El store NO almacena datos del pedido — solo estado de UI. Los datos vienen exclusivamente de `useOrderDetail` (TanStack Query).

```ts
// features/orders/store/orderDetailStore.ts
interface OrderDetailState {
  isCancelModalOpen: boolean
  openCancelModal: () => void
  closeCancelModal: () => void
}
```

### D4: OrderTimeline — animación con `@keyframes` de `@theme`, NO con librerías externas

**Decisión:** La animación de entrada de cada ítem del timeline se implementa con CSS puro usando el token `--animate-slide-in` definido en `@theme` del CSS base (patrón del skill `tailwind-design-system`). Cada ítem recibe un `animation-delay` inline proporcional a su índice.

**Alternativa descartada:** Framer Motion o React Spring. Descartadas porque añaden peso al bundle (~50kB) y la animación requerida es simple (slide-in + fade). Los tokens `@theme` son zero-cost en runtime.

**Consecuencia:** El CSS base debe incluir `--animate-slide-in: slide-in 0.3s ease-out` con el `@keyframes slide-in` correspondiente. Si el change anterior ya los definió, se reutilizan. Si no, se añaden en este change.

### D5: Estructura FSD — componentes en `features/orders/components/detail/`

**Decisión:** Los cinco componentes nuevos se agrupan en un subdirectorio `detail/` dentro de `features/orders/components/` para evitar mezclarlos con los componentes del listing.

```
features/orders/
├── components/
│   ├── OrderCard.tsx           ← existente (listing)
│   ├── OrderStatusBadge.tsx    ← existente (compartido)
│   ├── OrdersFilters.tsx       ← existente
│   ├── OrdersSkeleton.tsx      ← existente
│   ├── OrdersTable.tsx         ← existente
│   └── detail/
│       ├── OrderDetailHeader.tsx
│       ├── OrderDetailSkeleton.tsx
│       ├── OrderItemSnapshot.tsx
│       ├── OrderTimeline.tsx
│       ├── OrderActions.tsx
│       └── CancelOrderModal.tsx
├── hooks/
│   ├── useOrders.ts            ← existente
│   ├── useOrderDetail.ts       ← nuevo
│   ├── useCancelOrder.ts       ← nuevo
│   └── useAdvanceOrderState.ts ← nuevo
├── store/
│   ├── ordersFilterStore.ts    ← existente
│   └── orderDetailStore.ts     ← nuevo
└── types/
    └── index.ts                ← extendido con OrderDetail, OrderDetailItem, OrderHistorialItem
```

**Alternativa descartada:** Poner todos los componentes en el directorio raíz `components/`. Descartada porque con 11 componentes en total el directorio se vuelve difícil de navegar; el subdirectorio `detail/` es auto-explicativo.

### D6: Ruta única con layout condicional — NO dos páginas independientes

**Decisión:** La ruta `/pedidos/:id` usa un único componente `OrderDetailPage` que detecta el rol del usuario y condiciona las acciones (no la estructura visual). El panel admin usa `/admin/pedidos/:id` que renderiza el mismo `OrderDetailPage` con la prop `adminMode={true}`.

**Alternativa descartada:** Dos páginas completamente distintas `MyOrderDetailPage` y `AdminOrderDetailPage`. Descartada porque la estructura visual (header, snapshot, timeline, acciones) es idéntica en ambas; solo varían las acciones habilitadas.

**Consecuencia:** `OrderDetailPage` acepta una prop `adminMode?: boolean` que se pasa a `OrderActions` para determinar qué botones renderizar.

### D7: CancelOrderModal — Radix Dialog Primitive, NO div modal custom

**Decisión:** `CancelOrderModal` usa `@radix-ui/react-dialog` para garantizar focus trapping, `aria-modal`, `aria-labelledby` y `aria-describedby` sin implementación manual (patrón del skill `ui-design-system`).

**Alternativa descartada:** Modal implementado con `div` + `position:fixed` + `useEffect` para manejo de foco. Descartada porque es frágil, difícil de testear y viola el principio de accesibilidad WCAG 2.1 SC 2.1.2 (No Keyboard Trap).

**Consecuencia:** Radix Dialog ya es una dependencia transitiva del proyecto (via shadcn/ui). Si no está instalada directamente, el implementador debe verificar que `@radix-ui/react-dialog` está disponible antes de importar.

## Risks / Trade-offs

- **Tipo `usuario_email` en historial** → El backend puede no incluir el email en el historial (solo `usuario_responsable_id`). Mitigación: marcar `usuario_email: string | null` en el tipo e implementar un fallback visual "Usuario #ID" si el campo es null. Verificar con el schema `PedidoDetailResponse` real durante el apply.

- **`DELETE /api/v1/pedidos/{id}` devuelve el pedido cancelado, no 204** → Según el spec `orders-api`, el endpoint retorna HTTP 200 con el objeto. La mutation debe tipar la respuesta como `Order` y actualizar el cache con `queryClient.setQueryData` para reflejo inmediato antes de navegar. Mitigación: invalidar adicionalmente `['orders']` para que el listing se actualice.

- **`@keyframes slide-in` puede no existir en `@theme`** → Si el change anterior no lo definió, la animación silenciosamente no se aplica (sin error de compilación en Tailwind v4). Mitigación: el implementador debe verificar que el token `--animate-slide-in` existe en el CSS base y agregarlo si falta.

- **Radix Dialog puede no estar instalado como dependencia directa** → Si solo era transitiva, un cambio de versión podría romperlo. Mitigación: añadir `@radix-ui/react-dialog` explícitamente al `package.json` si no está listado.

## Migration Plan

1. Instalar dependencias si faltan: verificar `@radix-ui/react-dialog` en `frontend/package.json`.
2. Extender tipos en `features/orders/types/index.ts`.
3. Crear store Zustand `orderDetailStore.ts`.
4. Crear hooks `useOrderDetail`, `useCancelOrder`, `useAdvanceOrderState`.
5. Crear componentes en `features/orders/components/detail/`.
6. Crear `OrderDetailPage` con lazy loading en el router.
7. Registrar rutas en `app/router` (o equivalente): `/pedidos/:id` y `/admin/pedidos/:id`.
8. Escribir tests vitest en `features/orders/components/detail/__tests__/`.
9. Escribir tests E2E en `frontend/e2e/orders/order-detail.spec.ts`.

**Rollback:** Al ser rutas nuevas, el rollback es simplemente remover las rutas del router. No hay cambios destructivos en código existente (solo extensión de tipos y adición de archivos).

## Open Questions

1. ¿El backend incluye `usuario_email` en los items de `historial_estado_pedido` del response de `GET /api/v1/pedidos/{id}`, o solo `usuario_responsable_id`? → Determina si se necesita un `JOIN` en backend o un fallback UI.
2. ¿El endpoint `PATCH /api/v1/pedidos/{id}/estado` acepta el body `{ nuevo_estado_id: number }` o `{ estado_id: number }`? → Revisar el schema `PedidoEstadoUpdate` en `backend/pedidos/schemas.py`.
3. ¿`@radix-ui/react-dialog` está como dependencia directa en `frontend/package.json`? → Verificar antes de importar.
