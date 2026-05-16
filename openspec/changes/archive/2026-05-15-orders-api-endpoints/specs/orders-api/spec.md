## ADDED Requirements

### Requirement: CLIENT puede crear un pedido
El sistema SHALL permitir a un usuario autenticado con rol CLIENT crear un nuevo pedido a través de `POST /api/v1/pedidos`. La creación decrementa stock atómicamente, registra snapshots de precio y dirección, y crea una entrada de historial FSM.

#### Scenario: Creación exitosa de pedido
- **WHEN** CLIENT envía `POST /api/v1/pedidos` con `direccion_entrega_id`, `forma_pago_id`, `items` válidos
- **THEN** el sistema retorna HTTP 201 con el pedido creado (`PedidoResponse`) y header `Location: /api/v1/pedidos/{id}`

#### Scenario: Rate limit excedido
- **WHEN** CLIENT envía más de 10 requests a `POST /api/v1/pedidos` en una hora
- **THEN** el sistema retorna HTTP 429 con RFC 7807 `{ type, title: "Too Many Requests", status: 429, detail, instance }`

#### Scenario: Usuario no autenticado
- **WHEN** se envía `POST /api/v1/pedidos` sin JWT válido
- **THEN** el sistema retorna HTTP 401

#### Scenario: Rol insuficiente
- **WHEN** usuario con rol ADMIN intenta crear pedido (sin rol CLIENT)
- **THEN** el sistema retorna HTTP 403

#### Scenario: Stock insuficiente al crear
- **WHEN** se solicita más stock del disponible para algún producto
- **THEN** el sistema retorna HTTP 409 con RFC 7807 indicando producto_id, stock_actual, cantidad_solicitada

#### Scenario: Dirección de otro usuario
- **WHEN** se usa una `direccion_entrega_id` que pertenece a otro usuario
- **THEN** el sistema retorna HTTP 403 con RFC 7807

---

### Requirement: CLIENT puede listar sus pedidos con paginación
El sistema SHALL permitir a un usuario con rol CLIENT listar sus propios pedidos vía `GET /api/v1/pedidos`. La respuesta DEBE incluir `items`, `total`, `limit`, `offset`. Los pedidos con `eliminado_en` no NULL NO deben aparecer.

#### Scenario: Listado paginado por defecto
- **WHEN** CLIENT envía `GET /api/v1/pedidos` sin parámetros
- **THEN** el sistema retorna HTTP 200 con `{ items: [...], total: N, limit: 20, offset: 0 }` ordenado por `creado_en DESC`

#### Scenario: Paginación con parámetros
- **WHEN** CLIENT envía `GET /api/v1/pedidos?limit=5&offset=10`
- **THEN** el sistema retorna HTTP 200 con los pedidos en el rango [10..14] y `total` refleja el total real (no el tamaño de página)

#### Scenario: Aislamiento entre usuarios
- **WHEN** CLIENT-A hace `GET /api/v1/pedidos`
- **THEN** solo aparecen pedidos cuyo `usuario_id` coincide con CLIENT-A (nunca pedidos de otros usuarios)

#### Scenario: Pedidos soft-deleted no aparecen
- **WHEN** un pedido tiene `eliminado_en` no NULL
- **THEN** no aparece en el resultado de `GET /api/v1/pedidos`

---

### Requirement: CLIENT o ADMIN puede ver el detalle de un pedido
El sistema SHALL permitir ver el detalle completo de un pedido (con detalles de línea) vía `GET /api/v1/pedidos/{id}`. Un CLIENT solo puede ver sus propios pedidos; un ADMIN puede ver cualquiera.

#### Scenario: CLIENT accede a su propio pedido
- **WHEN** CLIENT envía `GET /api/v1/pedidos/{id}` donde el pedido le pertenece
- **THEN** el sistema retorna HTTP 200 con `PedidoDetailResponse` incluyendo `detalles`

#### Scenario: CLIENT intenta ver pedido de otro usuario
- **WHEN** CLIENT envía `GET /api/v1/pedidos/{id}` donde el pedido pertenece a otro usuario
- **THEN** el sistema retorna HTTP 403 con RFC 7807

#### Scenario: ADMIN puede ver cualquier pedido
- **WHEN** ADMIN envía `GET /api/v1/pedidos/{id}` de cualquier usuario
- **THEN** el sistema retorna HTTP 200 con el detalle completo

#### Scenario: Pedido no existe
- **WHEN** se solicita un `id` que no existe o tiene `eliminado_en` no NULL
- **THEN** el sistema retorna HTTP 404 con RFC 7807

---

### Requirement: ADMIN puede avanzar el estado FSM de un pedido
El sistema SHALL permitir a un ADMIN hacer transiciones de estado vía `PATCH /api/v1/pedidos/{id}/estado`. La transición DEBE seguir la matriz FSM definida en `service.VALID_TRANSITIONS`. La transición crea una entrada de auditoría inmutable.

#### Scenario: Transición válida
- **WHEN** ADMIN envía `PATCH /api/v1/pedidos/{id}/estado` con `nuevo_estado_id` válido según FSM
- **THEN** el sistema retorna HTTP 200 con el pedido actualizado y una nueva entrada en `historial_estado_pedido`

#### Scenario: Transición inválida según FSM
- **WHEN** ADMIN intenta una transición no permitida (ej: 5→3)
- **THEN** el sistema retorna HTTP 409 con RFC 7807 indicando `estado_actual` y `estado_solicitado`

#### Scenario: Non-ADMIN intenta avanzar estado
- **WHEN** usuario con rol CLIENT intenta `PATCH /pedidos/{id}/estado`
- **THEN** el sistema retorna HTTP 403

#### Scenario: Pedido en estado terminal (ENTREGADO o CANCELADO)
- **WHEN** ADMIN intenta avanzar un pedido en estado 5 (ENTREGADO) o 6 (CANCELADO)
- **THEN** el sistema retorna HTTP 409 indicando que no hay transiciones posibles desde el estado actual

---

### Requirement: CLIENT o ADMIN puede cancelar y eliminar (soft delete) un pedido
El sistema SHALL permitir cancelar un pedido vía `DELETE /api/v1/pedidos/{id}`. La cancelación revierte el stock, registra el historial FSM, y marca el pedido con `eliminado_en`. Un CLIENT solo puede cancelar pedidos en estado PENDIENTE. ADMIN puede cancelar desde cualquier estado cancelable. El pedido NO debe ser borrado físicamente de la BD (nunca hard delete).

#### Scenario: CLIENT cancela su pedido en estado PENDIENTE
- **WHEN** CLIENT envía `DELETE /api/v1/pedidos/{id}` y el pedido está en estado PENDIENTE
- **THEN** el sistema retorna HTTP 200 con el pedido cancelado, stock revertido, `eliminado_en` seteado

#### Scenario: CLIENT intenta cancelar pedido no-PENDIENTE
- **WHEN** CLIENT envía `DELETE /api/v1/pedidos/{id}` y el pedido no está en estado PENDIENTE
- **THEN** el sistema retorna HTTP 409 con RFC 7807 indicando el estado actual y que no se puede cancelar

#### Scenario: CLIENT intenta cancelar pedido de otro usuario
- **WHEN** CLIENT envía `DELETE /api/v1/pedidos/{id}` de otro usuario
- **THEN** el sistema retorna HTTP 403 con RFC 7807

#### Scenario: ADMIN cancela cualquier pedido cancelable
- **WHEN** ADMIN envía `DELETE /api/v1/pedidos/{id}` y el pedido está en estado PENDIENTE o CONFIRMADO
- **THEN** el sistema retorna HTTP 200 con el pedido cancelado y stock revertido

#### Scenario: Pedido ya eliminado (soft-deleted)
- **WHEN** se intenta acceder o cancelar un pedido con `eliminado_en` no NULL
- **THEN** el sistema retorna HTTP 404 (el pedido no existe desde la perspectiva del cliente)

---

### Requirement: Todos los endpoints de pedidos requieren autenticación y usan RFC 7807
El sistema SHALL rechazar con HTTP 401 toda request sin JWT válido a cualquier endpoint de `/api/v1/pedidos`. Todos los errores de negocio DEBEN seguir el formato RFC 7807 con campos `type`, `title`, `status`, `detail`, `instance`.

#### Scenario: Request sin Authorization header
- **WHEN** se envía cualquier request a `/api/v1/pedidos` sin header `Authorization`
- **THEN** el sistema retorna HTTP 401 con `WWW-Authenticate: Bearer`

#### Scenario: JWT expirado
- **WHEN** se envía request con JWT expirado
- **THEN** el sistema retorna HTTP 401

#### Scenario: Error de negocio usa RFC 7807
- **WHEN** el sistema genera cualquier error de negocio (409, 403, 422, 404)
- **THEN** el body de respuesta contiene `{ type, title, status, detail, instance }` con valores no vacíos
