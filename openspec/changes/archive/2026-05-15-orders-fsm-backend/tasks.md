## 0. Skills

- [ ] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — arquitectura Router→Service→UoW→Repository→Model, DDD patterns, uso de BaseRepository[T]
- [ ] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — SELECT FOR UPDATE, índices, concurrencia, ARRAY nativo PostgreSQL
- [ ] 0.3 Leer `.agents/skills/api-design/SKILL.md` — status codes RFC 7807, error responses 409/422/403/429
- [ ] 0.4 Leer `.agents/skills/rest-api-design-patterns/SKILL.md` — patrones REST, paginación, filtros
- [ ] 0.5 Leer `.agents/skills/jwt-security/SKILL.md` — get_current_user(), require_role(), validación de ownership
- [ ] 0.6 Leer `.agents/skills/post-change-verification/SKILL.md` — health check: pytest, mypy, black, flake8 pre-archive

## 1. Context Reading

- [ ] 1.1 Leer `backend/core/models.py` — confirmar campos exactos de Pedido, DetallePedido, HistorialEstadoPedido, EstadoPedido (IDs seedeados 1-6)
- [ ] 1.2 Leer `backend/infrastructure/uow.py` — confirmar propiedades existentes (pedidos, detalles_pedido, historial_estado_pedido, estados_pedido) y sus tipos actuales
- [ ] 1.3 Leer `backend/infrastructure/repositories/base_repository.py` — métodos disponibles: create(), get_by_id(), list_all(), update(), soft_delete(), execute_query()
- [ ] 1.4 Leer `backend/pedidos/service.py` — entender función validar_carrito() existente que no debe modificarse
- [ ] 1.5 Leer `backend/pedidos/schemas.py` — entender schemas existentes y los skeleton (PedidoCreate, DetallePedidoCreate, PedidoResponse, DetallePedidoResponse) que deben completarse
- [ ] 1.6 Leer `backend/pedidos/router.py` — confirmar que el endpoint /validar no debe tocarse
- [ ] 1.7 Leer `backend/direcciones/repository.py` — verificar si DireccionRepository tiene método para obtener dirección por id+usuario_id (ownership check)
- [ ] 1.8 Leer `backend/productos/repository.py` — verificar métodos existentes, especialmente get_by_ids()

## 2. Repository Layer

- [ ] 2.1 Crear `backend/pedidos/repository.py` con `PedidoRepository(BaseRepository[Pedido])`
- [ ] 2.2 Implementar `PedidoRepository.create_with_details()` — recibe Pedido + lista DetallePedido ya construidos con snapshots; inserta Pedido (flush para obtener ID), luego inserta cada DetallePedido (flush), retorna Pedido con ID asignado; NO decrementa stock (eso lo hace el service antes de llamar este método para separar responsabilidades)
- [ ] 2.3 Implementar `PedidoRepository.get_by_id_with_details()` — SELECT pedido JOIN detalle_pedido WHERE pedido.id=? AND pedido.eliminado_en IS NULL; retorna tuple(Pedido, list[DetallePedido])
- [ ] 2.4 Implementar `PedidoRepository.list_by_usuario()` — SELECT pedidos WHERE usuario_id=? AND eliminado_en IS NULL ORDER BY creado_en DESC LIMIT/OFFSET; acepta parámetros skip=0, limit=20
- [ ] 2.5 Implementar `PedidoRepository.update_estado()` — recibe pedido_id + nuevo estado_pedido_id; hace UPDATE pedidos SET estado_pedido_id=?, actualizado_en=now() WHERE id=?; retorna Pedido actualizado
- [ ] 2.6 Agregar `HistorialEstadoPedidoRepository` en el mismo archivo `pedidos/repository.py` — hereda BaseRepository[HistorialEstadoPedido]
- [ ] 2.7 Implementar `HistorialEstadoPedidoRepository.append()` — único método de escritura; llama BaseRepository.create(); no expone update() ni delete()
- [ ] 2.8 Implementar `HistorialEstadoPedidoRepository.list_by_pedido()` — SELECT historial WHERE pedido_id=? ORDER BY creado_en ASC; para auditoría

## 3. Stock Locking

- [ ] 3.1 Implementar `ProductoRepository.get_by_id_locked()` en `backend/productos/repository.py` — SELECT * FROM productos WHERE id=? FOR UPDATE; usa `select(Producto).where(Producto.id == id).with_for_update()` (RN-PE04)
- [ ] 3.2 Verificar que `get_by_id_locked()` también filtra `eliminado_en IS NULL` y `disponible=True`

## 4. Service Layer

- [ ] 4.1 Declarar constante `VALID_TRANSITIONS: dict[int, list[int]]` en `backend/pedidos/service.py` con la matriz FSM completa (D-03 del design)
- [ ] 4.2 Declarar constante `SYSTEM_ONLY_TARGETS: set[int] = {2}` — estados solo alcanzables por Sistema/webhook (CONFIRMADO, RN-FS02)
- [ ] 4.3 Implementar `create_pedido(request: PedidoCreate, usuario_id: int, uow: UnitOfWork) -> Pedido` en `pedidos/service.py`:
  - 4.3a Verificar que direccion_entrega_id pertenece al usuario (uow.direcciones); raise HTTP 403 si no
  - 4.3b Verificar forma_pago existe y está activa (uow.formas_pago); raise HTTP 422 si no
  - 4.3c Para cada item: llamar `uow.productos.get_by_id_locked(producto_id)` con FOR UPDATE
  - 4.3d Para cada item: validar disponible=True, eliminado_en IS NULL; raise HTTP 422 si producto inválido
  - 4.3e Para cada item: validar stock >= cantidad; raise HTTP 409 si insuficiente (RFC 7807 con producto_id)
  - 4.3f Construir lista DetallePedido con precio_snapshot=producto.precio_base, nombre_snapshot=producto.nombre
  - 4.3g Decrementar producto.stock_cantidad -= item.cantidad; llamar uow.session.add(producto) + flush
  - 4.3h Serializar dirección a JSON string para direccion_snapshot (alias, linea1, ciudad, codigo_postal)
  - 4.3i Calcular total = sum(detalle.precio_snapshot * detalle.cantidad)
  - 4.3j Construir Pedido(usuario_id, direccion_entrega_id, forma_pago_id, estado_pedido_id=1, total, observacion, direccion_snapshot)
  - 4.3k Llamar uow.pedidos.create_with_details(pedido, detalles)
  - 4.3l Escribir HistorialEstadoPedido con estado_anterior_id=None, estado_nuevo_id=1, usuario_responsable_id=usuario_id
  - 4.3m Retornar Pedido creado
- [ ] 4.4 Implementar `avanzar_estado(pedido_id: int, nuevo_estado_id: int, usuario_id: int, uow: UnitOfWork) -> Pedido`:
  - 4.4a Obtener pedido con get_by_id(); raise HTTP 404 si no existe o soft-deleted
  - 4.4b Verificar que nuevo_estado_id está en VALID_TRANSITIONS[pedido.estado_pedido_id]; raise HTTP 409 si inválido
  - 4.4c Si nuevo_estado_id en SYSTEM_ONLY_TARGETS: la validación de rol ocurre en router, pero documentar raise HTTP 403 aquí si se pasa flag `is_system=False`
  - 4.4d Llamar uow.pedidos.update_estado(pedido_id, nuevo_estado_id)
  - 4.4e Escribir HistorialEstadoPedido con estado_anterior_id=old_estado, estado_nuevo_id=nuevo_estado_id, usuario_responsable_id=usuario_id
  - 4.4f Retornar Pedido actualizado
- [ ] 4.5 Implementar `cancelar(pedido_id: int, usuario_id: int, uow: UnitOfWork) -> Pedido`:
  - 4.5a Obtener pedido; raise HTTP 404 si no existe
  - 4.5b Verificar que 6 (CANCELADO) está en VALID_TRANSITIONS[pedido.estado_pedido_id]; raise HTTP 409 si ya es terminal
  - 4.5c Llamar uow.pedidos.update_estado(pedido_id, 6)
  - 4.5d Revertir stock: para cada DetallePedido del pedido, incrementar producto.stock_cantidad += detalle.cantidad
  - 4.5e Escribir HistorialEstadoPedido con estado_anterior_id=old_estado, estado_nuevo_id=6
  - 4.5f Retornar Pedido actualizado

## 5. Schemas

- [ ] 5.1 Agregar `HistorialEstadoResponse` en `pedidos/schemas.py` — campos: id, pedido_id, estado_anterior_id (Optional[int]), estado_nuevo_id, observacion (Optional[str]), usuario_responsable_id (Optional[int]), creado_en; con `model_config = {"from_attributes": True}`
- [ ] 5.2 Agregar `PedidoDetailResponse` en `pedidos/schemas.py` — extiende PedidoResponse agregando campo `detalles: list[DetallePedidoResponse]`
- [ ] 5.3 Agregar `AvanzarEstadoRequest` en `pedidos/schemas.py` — campos: nuevo_estado_id (int, ge=1, le=6), observacion (Optional[str] con sanitize_text validator)
- [ ] 5.4 Verificar que `PedidoCreate`, `DetallePedidoCreate`, `PedidoResponse`, `DetallePedidoResponse` ya existentes en schemas.py son correctos y no necesitan modificación (están en el skeleton del change anterior)

## 6. UoW Update

- [ ] 6.1 Importar `PedidoRepository` y `HistorialEstadoPedidoRepository` en `infrastructure/uow.py`
- [ ] 6.2 Actualizar propiedad `uow.pedidos` para retornar `PedidoRepository` en lugar de `BaseRepository[Pedido]`
- [ ] 6.3 Actualizar propiedad `uow.historial_estado_pedido` para retornar `HistorialEstadoPedidoRepository` en lugar de `BaseRepository[HistorialEstadoPedido]`
- [ ] 6.4 Mantener `uow.detalles_pedido` como `BaseRepository[DetallePedido]` (no requiere cambio — el repository lo usa directamente vía session)

## 7. Tests

- [ ] 7.1 Crear `backend/tests/test_orders_fsm.py` con tests unitarios/integración usando pytest + pytest-asyncio
- [ ] 7.2 Test: `test_create_pedido_success` — orden creada con snapshots correctos, stock decrementado, historial row con estado_anterior=None
- [ ] 7.3 Test: `test_create_pedido_insufficient_stock` — HTTP 409 cuando stock < cantidad, rollback verificado (stock no decrementado)
- [ ] 7.4 Test: `test_create_pedido_invalid_product` — HTTP 422 cuando producto.disponible=False o eliminado_en IS NOT NULL
- [ ] 7.5 Test: `test_valid_fsm_transition` — paramétrico sobre todas las transiciones válidas del VALID_TRANSITIONS dict
- [ ] 7.6 Test: `test_invalid_fsm_transition` — HTTP 409 para transiciones inválidas (ej: PENDIENTE→EN_CAMINO)
- [ ] 7.7 Test: `test_terminal_state_no_transition` — HTTP 409 intentando avanzar desde ENTREGADO o CANCELADO
- [ ] 7.8 Test: `test_cancelar_reverts_stock` — cancelar pedido incrementa stock de vuelta
- [ ] 7.9 Test: `test_historial_append_only` — verificar que HistorialEstadoPedidoRepository no tiene métodos update/delete
- [ ] 7.10 Test: `test_address_ownership_check` — HTTP 403 cuando direccion_entrega_id pertenece a otro usuario
- [ ] 7.11 Test: `test_precio_snapshot_matches_db` — precio_snapshot == producto.precio_base al momento de creación

## 8. Verification

- [ ] 8.1 Ejecutar `cd backend && python -m pytest tests/test_orders_fsm.py -v` — todos los tests pasan
- [ ] 8.2 Ejecutar `cd backend && python -m pytest --cov=pedidos --cov-report=term-missing` — cobertura ≥ 60% en módulo pedidos/
- [ ] 8.3 Ejecutar `cd backend && black --check pedidos/ infrastructure/uow.py` — sin errores de formato
- [ ] 8.4 Ejecutar `cd backend && flake8 pedidos/ infrastructure/uow.py` — sin errores de linting
- [ ] 8.5 Ejecutar `cd backend && python -m pytest` (suite completa) — tests existentes no regresionados
- [ ] 8.6 Verificar que el endpoint POST /api/v1/pedidos/validar sigue funcionando (no regresión del change anterior)
