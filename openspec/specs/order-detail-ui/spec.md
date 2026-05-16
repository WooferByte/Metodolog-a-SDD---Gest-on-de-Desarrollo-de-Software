## ADDED Requirements

### Requirement: CLIENT puede ver el detalle completo de su pedido en /pedidos/:id

El sistema SHALL renderizar en `/pedidos/:id` el detalle completo del pedido perteneciente al usuario autenticado con rol CLIENT. La página DEBE mostrar: header con número de pedido, fecha, total y badge de estado; snapshot congelado de cada producto al momento de compra; dirección de entrega capturada; timeline del historial FSM; y acciones contextuales según el estado del pedido. Solo el propietario del pedido puede acceder; cualquier otro usuario CLIENT que intente acceder a un pedido ajeno DEBE ser redirigido (el backend retorna 403 que dispara toast de error).

#### Scenario: CLIENT accede al detalle de su propio pedido
- **WHEN** un usuario autenticado con rol CLIENT navega a `/pedidos/:id` donde el pedido le pertenece
- **THEN** el sistema muestra `OrderDetailHeader` (número de pedido, fecha formateada, total en pesos argentinos, badge de estado), los `OrderItemSnapshot` con nombre_snapshot, cantidad, precio_snapshot y personalización de cada línea, la `OrderTimeline` con todos los cambios de estado en orden cronológico, y las `OrderActions` con los botones habilitados según el estado actual

#### Scenario: Skeleton visible mientras carga el detalle
- **WHEN** la petición a `GET /api/v1/pedidos/{id}` está en vuelo
- **THEN** el sistema muestra `OrderDetailSkeleton` con la forma aproximada del layout (header, items, timeline) en lugar de un spinner genérico o pantalla en blanco

#### Scenario: Pedido no existe o fue eliminado
- **WHEN** el backend responde HTTP 404 a `GET /api/v1/pedidos/{id}`
- **THEN** el sistema muestra un estado de error vacío con mensaje "Pedido no encontrado" y un CTA "Volver a mis pedidos" que navega a `/mis-pedidos`

#### Scenario: Usuario no autenticado intenta acceder al detalle
- **WHEN** un usuario no autenticado navega a `/pedidos/:id`
- **THEN** el sistema redirige a `/login` (comportamiento del guard `ProtectedRoute` existente)

---

### Requirement: ADMIN y PEDIDOS pueden ver el detalle de cualquier pedido en /admin/pedidos/:id

El sistema SHALL renderizar en `/admin/pedidos/:id` el detalle completo de cualquier pedido del sistema, accesible únicamente para usuarios con rol ADMIN o PEDIDOS. La estructura visual DEBE ser idéntica a la vista CLIENT, pero las `OrderActions` DEBEN mostrar el selector de cambio de estado (avanzar FSM) en lugar del botón de cancelar.

#### Scenario: ADMIN accede al detalle de un pedido de otro usuario
- **WHEN** un usuario con rol ADMIN navega a `/admin/pedidos/:id`
- **THEN** el sistema muestra el detalle completo del pedido (header, snapshots, timeline, acciones de admin)

#### Scenario: CLIENT intenta acceder a /admin/pedidos/:id → 403
- **WHEN** un usuario con rol CLIENT navega a `/admin/pedidos/:id`
- **THEN** el sistema redirige a `/403` (comportamiento del guard `ProtectedRoute` con roles permitidos)

#### Scenario: Error 500 del backend → toast error
- **WHEN** el backend responde HTTP 5xx a cualquier acción en la página de detalle
- **THEN** el interceptor Axios muestra un toast con mensaje de error del servidor y la página permanece en el estado anterior

---

### Requirement: OrderItemSnapshot muestra datos congelados al momento de compra

El sistema SHALL renderizar en `OrderItemSnapshot` exclusivamente los campos `nombre_snapshot`, `precio_snapshot` y `personalizacion` del `DetallePedido`. Está PROHIBIDO hacer una request adicional para obtener el producto actual (`GET /api/v1/productos/{id}`). El precio y nombre mostrados DEBEN ser los registrados al momento de creación del pedido, aunque el producto haya cambiado de precio o nombre desde entonces.

#### Scenario: Producto cuyo precio cambió desde la compra
- **WHEN** `precio_snapshot` del DetallePedido difiere del precio actual del producto en BD
- **THEN** `OrderItemSnapshot` muestra `precio_snapshot` (precio de compra), NO el precio actual

#### Scenario: Producto con personalización (personalizacion no vacío)
- **WHEN** `personalizacion` del DetallePedido es un array no vacío de IDs de ingredientes
- **THEN** `OrderItemSnapshot` muestra la lista de modificaciones (ej: "Sin cebolla, Extra queso") usando los nombres disponibles o un fallback "Personalización aplicada" si no hay nombres disponibles en el frontend

#### Scenario: Personalización vacía
- **WHEN** `personalizacion` del DetallePedido es un array vacío o null
- **THEN** `OrderItemSnapshot` no muestra ninguna sección de personalización

---

### Requirement: OrderTimeline muestra historial FSM append-only con animación

El sistema SHALL renderizar en `OrderTimeline` todos los items de `historial_estado_pedido` en orden cronológico ascendente (el más antiguo primero, el más reciente al final). Cada ítem DEBE mostrar: badge del estado nuevo, timestamp formateado, y el usuario responsable (email o fallback "Sistema" si `usuario_responsable_id` corresponde al sistema). Cada ítem DEBE tener una animación de entrada (`slide-in` con `animation-delay` proporcional al índice) usando tokens `@theme` de Tailwind v4.

#### Scenario: Pedido con un único historial (PENDIENTE inicial)
- **WHEN** el pedido tiene un único item en historial con `estado_anterior_id=null` y `estado_nuevo_id=1`
- **THEN** `OrderTimeline` muestra un único ítem "Pedido creado → PENDIENTE" con el timestamp de creación

#### Scenario: Pedido con múltiples transiciones de estado
- **WHEN** el pedido tiene N items en historial (N > 1)
- **THEN** `OrderTimeline` muestra N ítems en orden cronológico, cada uno con su badge, timestamp y usuario responsable, con animación de entrada escalonada

#### Scenario: Timeline accesible con teclado
- **WHEN** el usuario navega con Tab por `OrderTimeline`
- **THEN** cada ítem es alcanzable con teclado y el contenido es legible por screen readers (sin elementos decorativos sin `aria-hidden`)

---

### Requirement: OrderActions habilita/deshabilita acciones según FSM y rol

El sistema SHALL renderizar en `OrderActions` un conjunto de botones contextuales cuya habilitación depende del estado FSM del pedido y del rol del usuario autenticado. Las reglas son:

| Rol | Estado | Acción visible | Habilitada |
|-----|--------|----------------|------------|
| CLIENT | PENDIENTE (1) | Cancelar pedido | ✅ |
| CLIENT | Cualquier otro | Cancelar pedido | ❌ (disabled) |
| ADMIN/PEDIDOS | CONFIRMADO (2) | Avanzar a EN_PREPARACIÓN | ✅ |
| ADMIN/PEDIDOS | EN_PREPARACIÓN (3) | Avanzar a EN_CAMINO | ✅ |
| ADMIN/PEDIDOS | EN_CAMINO (4) | Avanzar a ENTREGADO | ✅ |
| ADMIN/PEDIDOS | ENTREGADO (5) o CANCELADO (6) | — (sin acciones) | — |

Un botón disabled DEBE tener `aria-disabled="true"` y un tooltip explicativo del motivo.

#### Scenario: CLIENT con pedido en PENDIENTE — botón cancelar habilitado
- **WHEN** se renderiza `OrderActions` para un CLIENT con `estado_pedido_id=1`
- **THEN** el botón "Cancelar pedido" es visible, enabled, y al hacer click abre `CancelOrderModal`

#### Scenario: CLIENT con pedido en EN_CAMINO — botón cancelar deshabilitado
- **WHEN** se renderiza `OrderActions` para un CLIENT con `estado_pedido_id=4`
- **THEN** el botón "Cancelar pedido" es visible pero `disabled` con `aria-disabled="true"` y tooltip "El pedido ya está en camino"

#### Scenario: ADMIN con pedido en EN_PREPARACIÓN — botón avanzar habilitado
- **WHEN** se renderiza `OrderActions` para un ADMIN con `estado_pedido_id=3`
- **THEN** el botón "Marcar como En camino" es visible y habilitado

#### Scenario: Estado terminal — sin acciones
- **WHEN** se renderiza `OrderActions` con `estado_pedido_id=5` (ENTREGADO) o `6` (CANCELADO)
- **THEN** `OrderActions` muestra un mensaje informativo "Este pedido está cerrado" sin botones de acción

---

### Requirement: CancelOrderModal requiere confirmación explícita con ARIA completo

El sistema SHALL mostrar un dialog de confirmación ANTES de ejecutar `DELETE /api/v1/pedidos/{id}`. El dialog DEBE implementarse con `@radix-ui/react-dialog` y DEBE tener: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` apuntando al título, `aria-describedby` apuntando al mensaje de advertencia. El foco DEBE moverse automáticamente al primer elemento interactivo al abrir. Al cerrar (confirmar o cancelar), el foco DEBE regresar al botón que abrió el dialog.

#### Scenario: Usuario confirma la cancelación
- **WHEN** el CLIENT hace click en "Sí, cancelar" dentro de `CancelOrderModal`
- **THEN** el sistema ejecuta `DELETE /api/v1/pedidos/{id}`, muestra un toast "Pedido cancelado correctamente", cierra el modal, e invalida el cache de TanStack Query para reflejar el nuevo estado

#### Scenario: Usuario cancela sin confirmar
- **WHEN** el CLIENT hace click en "No, mantener pedido" o presiona Escape
- **THEN** el modal se cierra sin ejecutar ninguna request y el foco regresa al botón "Cancelar pedido"

#### Scenario: Error al cancelar (ej: 409 — estado no cancelable)
- **WHEN** el backend responde HTTP 409 a `DELETE /api/v1/pedidos/{id}`
- **THEN** el modal se cierra, el interceptor Axios muestra un toast de error con el mensaje del backend, y el estado del pedido no cambia en la UI

#### Scenario: Accesibilidad de teclado en el modal
- **WHEN** `CancelOrderModal` está abierto
- **THEN** Tab y Shift+Tab navegan únicamente entre los elementos del modal (focus trap), y Escape cierra el modal sin confirmar

---

### Requirement: Tests E2E cubren acceso por rol, detalle visible y cancelación con confirmación

El sistema SHALL tener tests E2E en `frontend/e2e/orders/order-detail.spec.ts` que cubran al menos los siguientes escenarios usando el helper `loginAs` de la skill `testing-e2e-playwright` y `page.route` para mockear el backend.

#### Scenario: CLIENT ve el detalle de su pedido
- **WHEN** el test seedea auth como CLIENT y mockea `GET /api/v1/pedidos/1` con un pedido válido
- **THEN** navegar a `/pedidos/1` renderiza el header con el ID del pedido y la timeline es visible

#### Scenario: Timeline visible con múltiples estados
- **WHEN** el mock de `GET /api/v1/pedidos/1` incluye `historial` con 3 items
- **THEN** `OrderTimeline` renderiza exactamente 3 ítems en el DOM

#### Scenario: CLIENT cancela pedido PENDIENTE con confirmación
- **WHEN** el test seedea auth como CLIENT, el pedido tiene `estado_pedido_id=1`, y `DELETE /api/v1/pedidos/1` responde 200
- **THEN** hacer click en "Cancelar pedido", esperar el modal, hacer click en "Sí, cancelar", el toast "Pedido cancelado" es visible

#### Scenario: CLIENT sin auth → redirige a /login
- **WHEN** el test no seedea auth y navega a `/pedidos/1`
- **THEN** la URL cambia a `/login`

#### Scenario: CLIENT intenta acceder a /admin/pedidos/1 → redirige a /403
- **WHEN** el test seedea auth como CLIENT y navega a `/admin/pedidos/1`
- **THEN** la URL cambia a `/403`
