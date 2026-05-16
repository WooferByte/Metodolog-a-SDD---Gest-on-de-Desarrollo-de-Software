## Why

Con la pantalla `/mis-pedidos` (listado) ya operativa, los usuarios CLIENT pueden ver el resumen de sus pedidos pero no acceder al detalle completo: snapshots de productos congelados al momento de compra, historial cronológico de estados FSM, dirección de entrega capturada, ni acciones contextuales (cancelar si está PENDIENTE). Los ADMIN y PEDIDOS tampoco tienen una ruta `/pedidos/:id` para acceder al detalle desde el panel de gestión. Esta ausencia bloquea los flujos post-compra del CLIENT y el seguimiento operativo del equipo de pedidos.

## What Changes

- **Nueva ruta** `/pedidos/:id` (CLIENT) y `/admin/pedidos/:id` (ADMIN/PEDIDOS) — detalle completo de un pedido individual.
- **Nuevo componente** `OrderDetailHeader` — muestra usuario, fecha, total, badge de estado y número de pedido.
- **Nuevo componente** `OrderItemSnapshot` — renderiza cada `DetallePedido` con nombre, cantidad, precio y personalización congelados al momento de compra (nunca datos live del producto).
- **Nuevo componente** `OrderTimeline` — historial de estados FSM (`historial_estado_pedido`) con timestamps y usuario responsable, con animación de entrada por ítem.
- **Nuevo componente** `OrderActions` — botones contextuales habilitados/deshabilitados según estado FSM y rol del usuario (Cancelar para CLIENT-PENDIENTE, Cambiar Estado para ADMIN/PEDIDOS).
- **Nuevo componente** `CancelOrderModal` — dialog de confirmación con ARIA completo antes de ejecutar `DELETE /api/v1/pedidos/{id}`.
- **Nuevo hook** `useOrderDetail` — `useQuery` sobre `GET /api/v1/pedidos/{id}` con `OrderDetail` tipado.
- **Nueva mutation** `useCancelOrder` — `useMutation` sobre `DELETE /api/v1/pedidos/{id}` con invalidación de cache y toast.
- **Nueva mutation** `useAdvanceOrderState` — `useMutation` sobre `PATCH /api/v1/pedidos/{id}/estado` para ADMIN/PEDIDOS.
- **Nuevos tipos** `OrderDetail`, `OrderHistorialItem`, `OrderDetailItem` en `features/orders/types/`.
- **Tests E2E** Playwright: ver detalle, timeline visible, cancelar con confirmación, guard de rutas por rol.
- **Tests vitest**: componentes `OrderTimeline`, `OrderItemSnapshot`, `CancelOrderModal`.

## Capabilities

### New Capabilities

- `order-detail-ui`: Página de detalle de pedido con snapshot de productos, timeline FSM e acciones por rol. Cubre `GET /api/v1/pedidos/{id}` y `DELETE /api/v1/pedidos/{id}` desde el frontend.

### Modified Capabilities

- `orders-listing`: El componente `OrderCard` existente agrega el CTA "Ver detalle" que navega a `/pedidos/:id`. La modificación es a nivel de comportamiento de navegación (añade enlace), no a los requisitos del listing en sí.

## Impact

- **Frontend** — nuevo feature bajo `features/orders/`: 5 componentes nuevos, 2 hooks/mutations nuevos, tipos extendidos.
- **Páginas** — 2 nuevas entradas en el router (una para CLIENT, una para ADMIN/PEDIDOS).
- **TanStack Query** — nueva query key `['order-detail', id]`; invalidación de `['orders']` al cancelar o cambiar estado.
- **Sin cambios backend** — los endpoints ya están implementados y archivados en `orders-api-endpoints` y `orders-fsm-backend`.
- **Sin cambios Zustand** — no se añaden stores nuevos; `isAuthenticated` y rol del usuario se leen del store existente.
- **Dependencias** — no se instalan paquetes nuevos; Playwright ya está en el proyecto.
