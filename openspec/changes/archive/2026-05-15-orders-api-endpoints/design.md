## Context

El change `orders-fsm-backend` implementó `PedidoService` (create_pedido, avanzar_estado, cancelar, validar_carrito), `PedidoRepository` (create_with_details, get_by_id_with_details, list_by_usuario, update_estado), `HistorialEstadoPedidoRepository` (append), y todos los schemas Pydantic v2 necesarios.

El router actual (`backend/pedidos/router.py`) solo expone `POST /validar`. Este change agrega los 5 endpoints faltantes sin tocar la capa de negocio.

**Restricción arquitectónica clave**: el flujo es unidireccional — `Router → Service → UoW → Repository`. El router no puede tener lógica de negocio y el service ya lanza todas las `HTTPException`.

## Goals / Non-Goals

**Goals:**
- Exponer los 5 endpoints REST de pedidos siguiendo el patrón de `validar_carrito` existente
- Rate limiting en POST /pedidos: `10/hour` por usuario (slowapi, US-073)
- Ownership check en GET /{id} y DELETE /{id}: devolver 403 si el pedido no pertenece al usuario (salvo ADMIN)
- Paginación en GET /pedidos con `limit`, `offset`, `total` en el response body
- Soft delete en DELETE /{id}: setear `eliminado_en`, nunca hard delete
- RFC 7807 en todos los errores (ya garantizado por el service existente)
- `response_model` explícito en todos los endpoints (convención del proyecto)

**Non-Goals:**
- No modificar la lógica FSM ni el service
- No agregar endpoints de historial de estados (out of scope de este change)
- No implementar filtros avanzados en el listado (estado, fecha) — MVP
- No cambiar el schema de BD (no migración Alembic)
- No implementar frontend para pedidos

## Decisions

### D-01: Rate limiting por usuario_id (no por IP)

**Decisión**: Usar `key_func` personalizada que devuelve `str(current_user.id)` en el endpoint POST /pedidos.

**Razón**: El limiter global usa `get_remote_address` (por IP). Para pedidos, la especificación dice "10/usuario/hora" — dos usuarios distintos detrás del mismo NAT no deben compartir cuota. Requerimiento US-073.

**Alternativa descartada**: Rate limit por IP — viola el requisito de límite por usuario.

**Implementación**:
```python
def _limit_key(request: Request) -> str:
    # Extraer user_id del token; fallback a IP si no disponible
    user = request.state.user_id if hasattr(request.state, "user_id") else get_remote_address(request)
    return f"create_pedido:{user}"
```

**Nota práctica**: El enfoque más simple con slowapi es pasar `request: Request` al endpoint y usar el `current_user.id` resuelto como key string. Ver implementación en tarea 3.2.

### D-02: Ownership check — retornar 403 vs 404

**Decisión**: Retornar 403 cuando el pedido existe pero no pertenece al usuario. No revelar existencia del recurso con 404 a usuarios no autorizados.

**Razón**: El pedido existe en la BD, por lo que 404 sería incorrecto. Un CLIENT que intenta acceder al pedido de otro usuario debe saber que está prohibido, no que el recurso no existe (eso podría inducir a error en el frontend).

**Alternativa considerada**: Retornar 404 siempre para no revelar si el pedido existe (security by obscurity). Descartado porque complejiza el debugging y la UX.

**Excepción**: ADMIN puede acceder a cualquier pedido — el check de ownership se salta si el usuario tiene rol ADMIN.

### D-03: Paginación con `total` en response body

**Decisión**: Usar offset/limit con count separado. Response incluye `items`, `total`, `limit`, `offset`.

**Razón**: Dataset de pedidos por usuario es pequeño (decenas, no millones). La UI de historial de pedidos del cliente necesita mostrar "Página X de Y" — requiere `total`. Cursor-based sería over-engineering aquí.

**Schema**:
```python
class PaginatedPedidosResponse(BaseModel):
    items: list[PedidoResponse]
    total: int
    limit: int
    offset: int
```

**Nuevo método en repositorio**: `count_by_usuario(usuario_id) -> int` con `SELECT COUNT(*)` filtrado por `eliminado_en IS NULL`.

### D-04: DELETE como soft delete + cancelación FSM

**Decisión**: El endpoint DELETE /{id} realiza dos acciones en una sola transacción atómica:
1. Llama a `service.cancelar()` (que hace FSM → CANCELADO y revierte stock)
2. Luego setea `eliminado_en = utcnow()` en el pedido

**Razón**: Un pedido cancelado no debe aparecer en el listado activo del usuario. La cancelación y el soft delete son operativamente una sola acción desde la perspectiva del cliente.

**Restricción**: Solo CLIENT en estado PENDIENTE o ADMIN pueden cancelar. El service ya valida la transición FSM; si el estado no permite cancelar, lanza 409 antes de llegar al soft delete.

**Alternativa considerada**: Separar cancelación (PATCH /estado con CANCELADO=6) de ocultamiento. Descartado porque la UX esperada es que "eliminar" un pedido lo cancele y lo saque de la vista.

### D-05: PATCH /estado solo para ADMIN

**Decisión**: El endpoint `PATCH /pedidos/{id}/estado` requiere rol ADMIN. CLIENT no puede llamarlo directamente.

**Razón**: La transición a CONFIRMADO (estado_id=2) es SYSTEM_ONLY (RN-FS02 en la FSM). Las demás transiciones (3→4→5) son operativas y las hace el staff. Un CLIENT no debe poder auto-confirmar su pedido.

**Implementación**: `require_role(["ADMIN"])` como dependency. El service ya tiene el flag `is_system` para transiciones de sistema — el router ADMIN pasa `is_system=False`.

## Risks / Trade-offs

**[Risk] Race condition en rate limiting con múltiples workers**
→ Mitigation: slowapi usa en memoria por defecto. En producción con múltiples workers se necesitaría Redis como backend. Para el alcance del proyecto (1 worker uvicorn) esto es aceptable.

**[Risk] El soft delete en DELETE /{id} requiere acceso directo a `uow.pedidos` desde el router**
→ Mitigation: El router puede llamar a `service.cancelar()` y luego hacer el soft delete a través del UoW en el mismo bloque `async with uow`. No viola la arquitectura — el router coordina dos operaciones de service/UoW dentro de una sola transacción.

**[Risk] `count_by_usuario()` es una query adicional en cada listado**
→ Mitigation: La tabla `pedidos` por usuario es pequeña. `COUNT(*)` con índice en `usuario_id` y `eliminado_en` es O(1) en práctica. No justifica optimización adicional.

## Migration Plan

1. No hay cambios de schema — no se necesita migración Alembic.
2. El router se agrega a `pedidos/router.py` (el existente no se reemplaza).
3. El `include_router` ya está en `main.py` — los nuevos endpoints quedan disponibles automáticamente.
4. Despliegue: reiniciar uvicorn. Sin downtime adicional.

## Open Questions

- ¿El endpoint de historial de estados debe estar en este change o en uno posterior? → Fuera de scope por ahora.
- ¿Rate limiting debe usar Redis en staging? → Fuera de scope — usar memoria para el proyecto.
