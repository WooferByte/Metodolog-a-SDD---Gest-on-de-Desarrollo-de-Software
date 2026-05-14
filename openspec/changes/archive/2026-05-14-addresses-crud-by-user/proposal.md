## Why

Los usuarios autenticados necesitan gestionar sus propias direcciones de entrega para poder asociarlas a pedidos. Actualmente el módulo `backend/direcciones/` solo tiene schemas parciales (`schemas.py`) y carece de router, service y repository, por lo que no existe ningún endpoint funcional. Este change completa el CRUD completo de direcciones con las reglas de negocio definidas en el spec (RN-DI01, RN-DI02, RN-DI03).

## What Changes

- Crear `backend/direcciones/repository.py` — `DireccionRepository` heredando `BaseRepository[DireccionEntrega]`, con métodos específicos: `list_by_usuario`, `count_by_usuario`, `unset_predeterminada_for_usuario`
- Crear `backend/direcciones/service.py` — lógica RN-DI01 (auto-predeterminada en primera dirección), RN-DI02 (solo una predeterminada), RN-DI03 (ownership check 403)
- Crear `backend/direcciones/router.py` — 6 endpoints REST con `response_model` explícito en todos, JWT requerido
- Actualizar `backend/infrastructure/uow.py` — reemplazar el `BaseRepository[DireccionEntrega]` genérico por `DireccionRepository` especializado
- Actualizar `backend/main.py` — registrar `direcciones_router` en `/api/v1`
- Crear `backend/tests/test_direcciones.py` — mínimo 15 tests (service + router integration)
- Verificar migración Alembic: el campo `es_predeterminada` ya existe (migration 004); no se requiere nueva migración salvo índices de performance

## Capabilities

### New Capabilities

- `address-management`: CRUD completo de direcciones de entrega por usuario autenticado — crear, listar, obtener, actualizar, marcar predeterminada y soft-delete, con reglas RN-DI01/RN-DI02/RN-DI03

### Modified Capabilities

- `unit-of-work`: El UoW expone `uow.direcciones` como `DireccionRepository` (reemplaza `BaseRepository[DireccionEntrega]` genérico) para soportar queries específicas de ownership

## Impact

- **Backend**: nuevo módulo `backend/direcciones/` completo (repository, service, router)
- **UoW**: propiedad `direcciones_entrega` actualizada a `DireccionRepository`
- **main.py**: nuevo include_router para `direcciones_router`
- **Tests**: nuevo archivo `backend/tests/test_direcciones.py`
- **API**: 6 nuevos endpoints en `/api/v1/direcciones`
- **Migración**: no se necesita nueva migración (modelo y columna `es_predeterminada` ya existen en DB tras migration 004)
- **Índice recomendado**: `CREATE INDEX idx_direcciones_usuario ON direcciones_entrega(usuario_id) WHERE eliminado_en IS NULL` (performance de listado por usuario)
