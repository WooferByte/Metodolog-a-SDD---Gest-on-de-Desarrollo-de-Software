## MODIFIED Requirements

### Requirement: Transición PENDIENTE a CONFIRMADO es exclusiva del sistema de pagos
La FSM del pedido incluye la transición `PENDIENTE (1) → CONFIRMADO (2)` que es de uso exclusivo del sistema (no disponible para usuarios CLIENT ni roles STOCK/PEDIDOS). Esta transición SHALL ser disparada únicamente por el servicio de pagos (`pagos/service.py`) cuando MercadoPago confirma un pago como `approved` via webhook. El servicio de pedidos (`pedidos/service.py`) SHALL exponer una función `confirmar_pedido_por_pago(pedido_id, uow)` que ejecute esta transición con la misma lógica de `avanzar_estado` pero sin verificación de rol (es llamada de sistema a sistema dentro de la misma UoW).

#### Scenario: pagos/service llama confirmar_pedido_por_pago al recibir webhook approved
- **WHEN** el webhook de MP indica `estado=approved` y el pedido asociado está en PENDIENTE
- **THEN** `pagos/service.py` invoca `pedidos/service.confirmar_pedido_por_pago(pedido_id, uow)`, el pedido pasa a CONFIRMADO y se registra en `historial_estado_pedido` con `cambiado_por=None` (sistema)

#### Scenario: Intento de confirmar un pedido que no está en PENDIENTE lanza error
- **WHEN** `confirmar_pedido_por_pago` es invocado para un pedido en estado diferente a PENDIENTE
- **THEN** el service lanza `HTTPException(409)` con `detail="El pedido no está en estado PENDIENTE. Transición inválida."`

#### Scenario: Un CLIENT no puede solicitar la transición a CONFIRMADO vía API de pedidos
- **WHEN** un CLIENT autenticado envía una request de avance de estado que incluye CONFIRMADO como destino a través de `PUT /api/v1/pedidos/{id}/estado`
- **THEN** el sistema retorna HTTP 403 porque CONFIRMADO es SYSTEM_ONLY_TARGET y no puede ser solicitado por usuarios
