## ADDED Requirements

### Requirement: Cliente autenticado puede crear preferencia de pago para su pedido
El sistema SHALL permitir que un usuario autenticado con rol CLIENT cree una preferencia de pago en MercadoPago para un pedido propio en estado PENDIENTE. El sistema SHALL persistir el registro `Pago` en la BD con `estado=pending` y retornar el `init_point` (URL de redirección a MP) y el `preference_id`.

#### Scenario: Creación exitosa de preferencia para pedido propio en PENDIENTE
- **WHEN** un CLIENT autenticado envía `POST /api/v1/pagos/crear-preferencia` con `{ "pedido_id": <id_propio> }` y el pedido existe y está en PENDIENTE
- **THEN** el sistema crea la preferencia en MP SDK, persiste `Pago(pedido_id, preference_id, estado="pending", monto=total_pedido)` y retorna `{ "init_point": "https://...", "preference_id": "...", "pago_id": <id> }` con HTTP 201

#### Scenario: Rechazo si el pedido no pertenece al usuario autenticado
- **WHEN** un CLIENT autenticado envía `POST /api/v1/pagos/crear-preferencia` con `pedido_id` de otro usuario
- **THEN** el sistema retorna HTTP 403 con RFC 7807 `{ "type": "about:blank", "title": "Forbidden", "status": 403, "detail": "No tenés permisos para pagar este pedido." }`

#### Scenario: Rechazo si el pedido no está en estado PENDIENTE
- **WHEN** un CLIENT envía `POST /api/v1/pagos/crear-preferencia` con un `pedido_id` que existe pero cuyo estado no es PENDIENTE (e.g., CONFIRMADO, CANCELADO)
- **THEN** el sistema retorna HTTP 409 con RFC 7807 `{ "status": 409, "title": "Estado inválido", "detail": "Solo se puede pagar un pedido en estado PENDIENTE." }`

#### Scenario: Rechazo si el pedido no existe
- **WHEN** un CLIENT envía `POST /api/v1/pagos/crear-preferencia` con un `pedido_id` inexistente
- **THEN** el sistema retorna HTTP 404 con RFC 7807

#### Scenario: Rate limiting en crear-preferencia
- **WHEN** un mismo CLIENT autenticado realiza más de 5 requests a `POST /api/v1/pagos/crear-preferencia` en 60 segundos
- **THEN** el sistema retorna HTTP 429 con header `Retry-After`

### Requirement: Inicialización del SDK de MercadoPago usando MP_ACCESS_TOKEN
El sistema SHALL inicializar el SDK de MercadoPago una sola vez usando la variable de entorno `MP_ACCESS_TOKEN`. Si `MP_ACCESS_TOKEN` no está configurada, el sistema SHALL fallar al arrancar con un error explícito de configuración.

#### Scenario: SDK inicializado correctamente al arrancar
- **WHEN** la aplicación arranca con `MP_ACCESS_TOKEN` configurada
- **THEN** el SDK queda disponible como dependencia FastAPI y los endpoints de pagos pueden usarlo

#### Scenario: Error de configuración si MP_ACCESS_TOKEN ausente
- **WHEN** la aplicación arranca sin `MP_ACCESS_TOKEN` en las variables de entorno
- **THEN** la aplicación falla al arrancar con `ValueError: MP_ACCESS_TOKEN no configurado`
