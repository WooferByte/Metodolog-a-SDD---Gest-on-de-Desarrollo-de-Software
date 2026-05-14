# Design — addresses-crud-by-user

## Arquitectura General

Flujo estricto según AGENTS.md:

```
Router → Service → UoW → DireccionRepository → DireccionEntrega (model)
```

Ninguna capa viola la dirección del flujo. El router solo parsea HTTP y delega. El service contiene toda la lógica de negocio y lanza `HTTPException`. El repository accede a BD sin lógica de negocio. El UoW gestiona la transacción.

## Modelo Existente — DireccionEntrega

Confirmado en `backend/core/models.py` (líneas 150–172):

```python
class DireccionEntrega(SQLModel, table=True):
    __tablename__ = "direcciones_entrega"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id")
    alias: str
    linea1: str
    piso: Optional[str] = None
    departamento: Optional[str] = None
    ciudad: str
    codigo_postal: str
    referencia: Optional[str] = None
    es_predeterminada: bool = False        # ← campo confirmado (migration 004)
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None
```

**INC-02 resuelto**: el campo es `es_predeterminada` (renombrado de `es_principal` en migration 004). Los schemas en `backend/direcciones/schemas.py` ya usan el nombre correcto.

## Schemas (ya existen en `backend/direcciones/schemas.py`)

Los schemas `DireccionCreate`, `DireccionUpdate`, `DireccionResponse` ya están implementados correctamente con:
- Validación Pydantic v2 (`field_validator`, `Field(min_length=..., max_length=...)`)
- Sanitización XSS en campos de texto libre
- `model_config = {"from_attributes": True}` en `DireccionResponse`

No se requiere modificar `schemas.py`.

## DireccionRepository — `backend/direcciones/repository.py`

Hereda `BaseRepository[DireccionEntrega]`. Agrega métodos específicos de ownership:

```python
class DireccionRepository(BaseRepository[DireccionEntrega]):
    def __init__(self, session) -> None:
        super().__init__(session, DireccionEntrega)

    async def list_by_usuario(self, usuario_id: int) -> list[DireccionEntrega]:
        """Listar direcciones activas del usuario, ordenadas por creado_en DESC."""
        stmt = (
            select(DireccionEntrega)
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.eliminado_en.is_(None))
            .order_by(DireccionEntrega.creado_en.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_active_by_usuario(self, usuario_id: int) -> int:
        """Contar direcciones activas del usuario (para RN-DI01)."""
        stmt = (
            select(func.count(DireccionEntrega.id))
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.eliminado_en.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def unset_predeterminada_for_usuario(self, usuario_id: int) -> None:
        """Desmarcar todas las direcciones predeterminadas del usuario (para RN-DI02)."""
        stmt = (
            update(DireccionEntrega)
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.es_predeterminada.is_(True))
            .where(DireccionEntrega.eliminado_en.is_(None))
            .values(es_predeterminada=False, actualizado_en=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def get_latest_active_by_usuario(self, usuario_id: int) -> Optional[DireccionEntrega]:
        """Obtener la dirección más reciente del usuario (para soft-delete de predeterminada)."""
        stmt = (
            select(DireccionEntrega)
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.eliminado_en.is_(None))
            .order_by(DireccionEntrega.creado_en.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

## DireccionService — `backend/direcciones/service.py`

```
Reglas de negocio:
- RN-DI01: primera dirección → es_predeterminada=True automático
- RN-DI02: solo una predeterminada por usuario
- RN-DI03: ownership — 403 si usuario_id del JWT != direccion.usuario_id
```

Funciones públicas:

| Función | Descripción |
|---------|-------------|
| `list_direcciones(uow, usuario_id)` | Listar todas las activas del usuario |
| `get_direccion(uow, id, usuario_id)` | Get por ID con ownership check (403) |
| `create_direccion(uow, data, usuario_id)` | Crear con auto-predeterminada (RN-DI01) |
| `update_direccion(uow, id, data, usuario_id)` | Update parcial con ownership check |
| `set_predeterminada(uow, id, usuario_id)` | Marcar predeterminada, desmarcar resto (RN-DI02) |
| `delete_direccion(uow, id, usuario_id)` | Soft-delete, reasignar predeterminada si era la default |

**Ownership helper privado:**

```python
async def _get_or_403(uow, direccion_id, usuario_id) -> DireccionEntrega:
    direccion = await uow.direcciones.get_by_id(direccion_id)
    if direccion is None:
        raise HTTPException(404, ...)
    if direccion.usuario_id != usuario_id:
        raise HTTPException(403, ...)
    return direccion
```

**Lógica soft-delete con reasignación de predeterminada:**

```python
async def delete_direccion(uow, id, usuario_id):
    direccion = await _get_or_403(uow, id, usuario_id)
    era_predeterminada = direccion.es_predeterminada
    await uow.direcciones.soft_delete(id)
    if era_predeterminada:
        # Reasignar a la más reciente restante
        next_default = await uow.direcciones.get_latest_active_by_usuario(usuario_id)
        if next_default:
            next_default.es_predeterminada = True
            await uow.direcciones.update(next_default)
```

## DireccionRouter — `backend/direcciones/router.py`

Prefijo: `/direcciones` (se registra en main.py con `/api/v1`)

| Method | Path | Status | Auth |
|--------|------|--------|------|
| POST | `/direcciones` | 201 Created | `get_current_user` |
| GET | `/direcciones` | 200 OK | `get_current_user` |
| GET | `/direcciones/{id}` | 200 OK | `get_current_user` |
| PUT | `/direcciones/{id}` | 200 OK | `get_current_user` |
| PATCH | `/direcciones/{id}/predeterminada` | 200 OK | `get_current_user` |
| DELETE | `/direcciones/{id}` | 204 No Content | `get_current_user` |

**Todos los endpoints**:
- Requieren `get_current_user` de `core.dependencies` (no `infrastructure.dependencies`)
- Tienen `response_model` explícito (`DireccionResponse` o `list[DireccionResponse]`)
- Usan `Depends(get_uow)` de `infrastructure.uow`
- El router NO contiene lógica de negocio — solo llama al service

## UoW — Actualización `backend/infrastructure/uow.py`

Reemplazar la propiedad `direcciones_entrega` (BaseRepository genérico) por `direcciones` (DireccionRepository):

```python
# Agregar import al inicio
from direcciones.repository import DireccionRepository

# Reemplazar propiedad:
@property
def direcciones(self) -> DireccionRepository:
    """Repository para DireccionEntrega con métodos de ownership."""
    if "direcciones" not in self._repositories:
        self._repositories["direcciones"] = DireccionRepository(self.session)
    return self._repositories["direcciones"]
```

**Nota**: La propiedad `direcciones_entrega` existente queda deprecada y puede eliminarse en este change si no hay otros módulos que la usen (verificar con grep antes de eliminar).

## main.py — Registro del Router

```python
from direcciones.router import router as direcciones_router
app.include_router(direcciones_router, prefix="/api/v1")
```

## Migración Alembic

**No se requiere nueva migración de esquema**. El modelo `DireccionEntrega` y el campo `es_predeterminada` ya existen (confirmado por `backend/alembic/versions/004_rename_es_principal_to_es_predeterminada.py`).

**Migración recomendada (performance)**: agregar índice parcial para listado por usuario:

```sql
CREATE INDEX CONCURRENTLY idx_direcciones_entrega_usuario
ON direcciones_entrega(usuario_id)
WHERE eliminado_en IS NULL;
```

Esta migración mejora la performance de `list_by_usuario` y debe crearse como `009_add_direcciones_entrega_usuario_index.py`.

## Tests — `backend/tests/test_direcciones.py`

Estrategia: mocks de UoW/DireccionRepository (igual que `test_categorias.py`). Sin hit real a BD.

Cobertura mínima de 15 tests:

| # | Descripción |
|---|-------------|
| 1 | `create_direccion` — primera dirección → auto-predeterminada=True (RN-DI01) |
| 2 | `create_direccion` — segunda dirección → no auto-predeterminada |
| 3 | `create_direccion` — con es_predeterminada=True explícito → llama a unset_predeterminada_for_usuario |
| 4 | `list_direcciones` — retorna solo las del usuario |
| 5 | `get_direccion` — encontrada y es del usuario → 200 |
| 6 | `get_direccion` — no encontrada → 404 |
| 7 | `get_direccion` — de otro usuario → 403 (RN-DI03) |
| 8 | `update_direccion` — update parcial exitoso |
| 9 | `update_direccion` — de otro usuario → 403 (RN-DI03) |
| 10 | `set_predeterminada` — desmarca todas antes de marcar nueva (RN-DI02) |
| 11 | `set_predeterminada` — dirección de otro usuario → 403 |
| 12 | `delete_direccion` — soft delete exitoso (no predeterminada) |
| 13 | `delete_direccion` — era predeterminada → reasigna a siguiente |
| 14 | `delete_direccion` — era predeterminada, no hay más → no reasigna |
| 15 | Router — `POST /direcciones` sin token → 401 |
| 16 | Router — `GET /direcciones` sin token → 401 |
| 17 | Router — `DELETE /direcciones/{id}` sin token → 401 |

## Dependencias Externas

No se requieren dependencias nuevas. Todo el stack necesario está instalado:
- `fastapi`, `sqlmodel`, `sqlalchemy` (async)
- `pydantic` v2
- `pytest`, `pytest-asyncio` para tests

## Checklist de Seguridad

- [ ] JWT validado con `get_current_user()` en TODOS los endpoints
- [ ] Ownership verificado por `usuario_id` del JWT en service (no en router)
- [ ] Sin concatenación SQL directa — solo SQLAlchemy ORM
- [ ] Soft delete con `eliminado_en` — sin hard delete
- [ ] `service.py` nunca llama `session.commit()` directamente
- [ ] `router.py` tiene `response_model` explícito en todos los endpoints
- [ ] Errores RFC 7807 en HTTPException del service
