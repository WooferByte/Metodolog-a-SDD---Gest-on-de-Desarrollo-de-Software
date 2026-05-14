# Tasks — addresses-crud-by-user

## 0. Skills

- [ ] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — patrones DDD, Repository, UseCase, Entity; flujo Router→Service→UoW→Repository→Model
- [ ] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — índices parciales, queries parametrizadas, soft-delete patterns en PostgreSQL
- [ ] 0.3 Leer `.agents/skills/api-design/SKILL.md` — status codes HTTP correctos, ownership checks, patrones de autorización en endpoints REST
- [ ] 0.4 Leer `.agents/skills/post-change-verification/SKILL.md` — checklist de verificación post-apply antes de archivar

---

## 1. Verificación Pre-implementación

- [ ] 1.1 Leer `backend/core/models.py` líneas 150–172 — confirmar campos de `DireccionEntrega` y que `es_predeterminada` existe (INC-02 ya resuelto en migration 004)
- [ ] 1.2 Leer `backend/infrastructure/uow.py` — identificar propiedad `direcciones_entrega` existente (BaseRepository genérico) para reemplazarla
- [ ] 1.3 Leer `backend/direcciones/schemas.py` — confirmar que `DireccionCreate`, `DireccionUpdate`, `DireccionResponse` ya están correctos (no modificar)
- [ ] 1.4 Leer `backend/main.py` — identificar sección de routers para agregar `direcciones_router`
- [ ] 1.5 Verificar que no existe `backend/direcciones/repository.py`, `service.py`, `router.py` — si existen, leerlos antes de sobreescribir
- [ ] 1.6 Verificar que no hay otros módulos usando `uow.direcciones_entrega` con grep — si los hay, actualizar las referencias

---

## 2. DireccionRepository — `backend/direcciones/repository.py`

- [ ] 2.1 Crear `backend/direcciones/repository.py` con clase `DireccionRepository(BaseRepository[DireccionEntrega])`
- [ ] 2.2 Implementar `__init__(self, session)` llamando a `super().__init__(session, DireccionEntrega)`
- [ ] 2.3 Implementar `list_by_usuario(self, usuario_id: int) -> list[DireccionEntrega]`:
  - Query: `SELECT ... FROM direcciones_entrega WHERE usuario_id=? AND eliminado_en IS NULL ORDER BY creado_en DESC`
  - Usar SQLAlchemy ORM (no SQL raw)
- [ ] 2.4 Implementar `count_active_by_usuario(self, usuario_id: int) -> int`:
  - `SELECT COUNT(id) WHERE usuario_id=? AND eliminado_en IS NULL`
  - Para RN-DI01 (primera dirección)
- [ ] 2.5 Implementar `unset_predeterminada_for_usuario(self, usuario_id: int) -> None`:
  - `UPDATE direcciones_entrega SET es_predeterminada=False, actualizado_en=NOW() WHERE usuario_id=? AND es_predeterminada=True AND eliminado_en IS NULL`
  - Usar `sqlalchemy.update()` (bulk update — no cargar todos en memoria)
  - Para RN-DI02
- [ ] 2.6 Implementar `get_latest_active_by_usuario(self, usuario_id: int) -> Optional[DireccionEntrega]`:
  - `SELECT ... WHERE usuario_id=? AND eliminado_en IS NULL ORDER BY creado_en DESC LIMIT 1`
  - Para reasignación de predeterminada en soft-delete

---

## 3. DireccionService — `backend/direcciones/service.py`

- [ ] 3.1 Crear `backend/direcciones/service.py`
- [ ] 3.2 Implementar helper privado `_get_or_403(uow, direccion_id, usuario_id) -> DireccionEntrega`:
  - `await uow.direcciones.get_by_id(id)` → si None → raise 404 RFC 7807
  - `if direccion.usuario_id != usuario_id` → raise 403 RFC 7807
  - Retornar la dirección si todo OK
- [ ] 3.3 Implementar `list_direcciones(uow, usuario_id) -> list[DireccionEntrega]`:
  - Llamar `await uow.direcciones.list_by_usuario(usuario_id)`
- [ ] 3.4 Implementar `get_direccion(uow, id, usuario_id) -> DireccionEntrega`:
  - Llamar `_get_or_403(uow, id, usuario_id)`
- [ ] 3.5 Implementar `create_direccion(uow, data: DireccionCreate, usuario_id: int) -> DireccionEntrega`:
  - Contar direcciones activas del usuario: `count = await uow.direcciones.count_active_by_usuario(usuario_id)`
  - Si `count == 0` → forzar `es_predeterminada=True` (RN-DI01)
  - Si `data.es_predeterminada=True` y `count > 0` → llamar `unset_predeterminada_for_usuario` (RN-DI02)
  - Crear `DireccionEntrega(**data.model_dump(), usuario_id=usuario_id)`
  - Llamar `await uow.direcciones.create(direccion)`
- [ ] 3.6 Implementar `update_direccion(uow, id, data: DireccionUpdate, usuario_id) -> DireccionEntrega`:
  - Llamar `_get_or_403(uow, id, usuario_id)`
  - Si `data.es_predeterminada=True` → llamar `unset_predeterminada_for_usuario` (RN-DI02)
  - Aplicar solo campos no-None: `update_data = data.model_dump(exclude_none=True)`
  - Para cada campo → `setattr(direccion, field, value)`
  - Llamar `await uow.direcciones.update(direccion)`
- [ ] 3.7 Implementar `set_predeterminada(uow, id, usuario_id) -> DireccionEntrega`:
  - Llamar `_get_or_403(uow, id, usuario_id)` → obtener dirección
  - Llamar `await uow.direcciones.unset_predeterminada_for_usuario(usuario_id)` (RN-DI02)
  - Setear `direccion.es_predeterminada = True`
  - Llamar `await uow.direcciones.update(direccion)`
- [ ] 3.8 Implementar `delete_direccion(uow, id, usuario_id) -> None`:
  - Llamar `_get_or_403(uow, id, usuario_id)`
  - Guardar `era_predeterminada = direccion.es_predeterminada`
  - Llamar `await uow.direcciones.soft_delete(id)`
  - Si `era_predeterminada=True`:
    - Llamar `get_latest_active_by_usuario(usuario_id)` → si existe, setear `es_predeterminada=True` y llamar `update`
- [ ] 3.9 Verificar que NINGUNA función del service llama `session.commit()` directamente

---

## 4. DireccionRouter — `backend/direcciones/router.py`

- [ ] 4.1 Crear `backend/direcciones/router.py` con `router = APIRouter(prefix="/direcciones", tags=["Direcciones"])`
- [ ] 4.2 Importar `get_current_user` desde `core.dependencies` (NO desde `infrastructure.dependencies`)
- [ ] 4.3 Importar `get_uow` y `UnitOfWork` desde `infrastructure.uow`
- [ ] 4.4 Implementar `POST /` con `response_model=DireccionResponse`, status_code=201:
  ```python
  @router.post("", response_model=DireccionResponse, status_code=status.HTTP_201_CREATED)
  async def create_direccion(
      data: DireccionCreate,
      current_user: Usuario = Depends(get_current_user),
      uow: UnitOfWork = Depends(get_uow),
  ) -> DireccionResponse:
      async with uow:
          return await service.create_direccion(uow, data, current_user.id)
  ```
- [ ] 4.5 Implementar `GET /` con `response_model=list[DireccionResponse]`, status_code=200
- [ ] 4.6 Implementar `GET /{id}` con `response_model=DireccionResponse`, status_code=200
- [ ] 4.7 Implementar `PUT /{id}` con `response_model=DireccionResponse`, status_code=200
- [ ] 4.8 Implementar `PATCH /{id}/predeterminada` con `response_model=DireccionResponse`, status_code=200
- [ ] 4.9 Implementar `DELETE /{id}` con `response_model=None`, status_code=204:
  - Retornar `Response(status_code=204)` explícitamente (no retornar body)
- [ ] 4.10 Verificar que el router NO contiene lógica de negocio — solo llama a funciones del service

---

## 5. UoW — Actualizar `backend/infrastructure/uow.py`

- [ ] 5.1 Agregar import al inicio: `from direcciones.repository import DireccionRepository`
- [ ] 5.2 Agregar nueva propiedad `direcciones` (reemplaza `direcciones_entrega`):
  ```python
  @property
  def direcciones(self) -> DireccionRepository:
      """Repository para DireccionEntrega con métodos de ownership."""
      if "direcciones" not in self._repositories:
          self._repositories["direcciones"] = DireccionRepository(self.session)
      return self._repositories["direcciones"]
  ```
- [ ] 5.3 Mantener o eliminar la propiedad `direcciones_entrega` según resultado del grep del paso 1.6
  - Si no hay otras referencias → eliminarla para evitar confusión
  - Si hay referencias → mantenerla temporalmente y agregar `direcciones` como adicional

---

## 6. main.py — Registrar Router

- [ ] 6.1 Agregar import en la sección de routers:
  ```python
  from direcciones.router import router as direcciones_router
  ```
- [ ] 6.2 Agregar `app.include_router(direcciones_router, prefix="/api/v1")`
- [ ] 6.3 Verificar que el servidor arranca sin errores de import circular

---

## 7. Migración Alembic — `backend/alembic/versions/009_add_direcciones_entrega_usuario_index.py`

- [ ] 7.1 Crear archivo `009_add_direcciones_entrega_usuario_index.py`:
  ```python
  """Add partial index on direcciones_entrega(usuario_id) for active records

  Revision ID: 009_add_direcciones_entrega_usuario_index
  Revises: 008_add_productos_index
  """
  from alembic import op

  revision = "009_add_direcciones_entrega_usuario_index"
  down_revision = "008_add_productos_index"
  branch_labels = None
  depends_on = None

  def upgrade() -> None:
      op.create_index(
          "idx_direcciones_entrega_usuario",
          "direcciones_entrega",
          ["usuario_id"],
          postgresql_where="eliminado_en IS NULL",
      )

  def downgrade() -> None:
      op.drop_index("idx_direcciones_entrega_usuario", table_name="direcciones_entrega")
  ```
- [ ] 7.2 Verificar que `down_revision` apunta correctamente al último hash activo (`008_add_productos_index`)

---

## 8. Tests — `backend/tests/test_direcciones.py`

- [ ] 8.1 Crear `backend/tests/test_direcciones.py` con imports: `pytest`, `AsyncMock`, `MagicMock`, `HTTPException`, `TestClient`, `sys.path.insert(0, ...)`
- [ ] 8.2 Crear helper `_make_direccion(id, usuario_id, es_predeterminada, eliminado_en)` que retorna MagicMock
- [ ] 8.3 Crear helper `_make_uow(repo)` que retorna MagicMock de UnitOfWork con `uow.direcciones = repo`
- [ ] 8.4 Test 1: `create_direccion` — primera dirección (count=0) → `es_predeterminada=True` automático
- [ ] 8.5 Test 2: `create_direccion` — segunda dirección (count=1), body `es_predeterminada=False` → no llamar a `unset_predeterminada_for_usuario`
- [ ] 8.6 Test 3: `create_direccion` — segunda dirección con `es_predeterminada=True` → llamar `unset_predeterminada_for_usuario`
- [ ] 8.7 Test 4: `list_direcciones` — retorna lista del usuario (sin tocar otras)
- [ ] 8.8 Test 5: `get_direccion` — ID existe, es del usuario → retorna dirección
- [ ] 8.9 Test 6: `get_direccion` — ID no existe → HTTPException 404
- [ ] 8.10 Test 7: `get_direccion` — ID de otro usuario → HTTPException 403 (RN-DI03)
- [ ] 8.11 Test 8: `update_direccion` — update parcial exitoso (solo alias)
- [ ] 8.12 Test 9: `update_direccion` — de otro usuario → HTTPException 403
- [ ] 8.13 Test 10: `set_predeterminada` — llama a `unset_predeterminada_for_usuario` y setea `es_predeterminada=True` (RN-DI02)
- [ ] 8.14 Test 11: `set_predeterminada` — de otro usuario → HTTPException 403
- [ ] 8.15 Test 12: `delete_direccion` — no predeterminada → soft_delete sin reasignación
- [ ] 8.16 Test 13: `delete_direccion` — era predeterminada, hay siguiente → reasigna predeterminada
- [ ] 8.17 Test 14: `delete_direccion` — era predeterminada, no hay más → sin reasignación
- [ ] 8.18 Test 15: Router `POST /api/v1/direcciones` sin token → 401
- [ ] 8.19 Test 16: Router `GET /api/v1/direcciones` sin token → 401
- [ ] 8.20 Test 17: Router `DELETE /api/v1/direcciones/1` sin token → 401

---

## 9. Verificación Post-implementación (skill: post-change-verification)

- [ ] 9.1 Backend lint: `.venv/Scripts/black --check .` y `.venv/Scripts/flake8 .` sin errores
- [ ] 9.2 Tests: `.venv/Scripts/pytest backend/tests/test_direcciones.py -v` → todos pasan
- [ ] 9.3 Coverage: `.venv/Scripts/pytest --cov=. --cov-report=term-missing` → backend ≥ 60%
- [ ] 9.4 Migración: `.venv/Scripts/alembic upgrade head` → termina sin error
- [ ] 9.5 Alembic current: `.venv/Scripts/alembic current` → muestra `009_add_direcciones_entrega_usuario_index (head)`
- [ ] 9.6 Servidor: `.venv/Scripts/uvicorn main:app --reload` → "Application startup complete"
- [ ] 9.7 Swagger: verificar que aparecen los 6 endpoints de `/api/v1/direcciones` en `http://localhost:8000/docs`
- [ ] 9.8 Test manual — crear dirección:
  ```bash
  # Obtener token
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@foodstore.com","password":"admin123456"}'
  # Crear dirección
  curl -X POST http://localhost:8000/api/v1/direcciones \
    -H "Authorization: Bearer <TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"alias":"Casa","linea1":"Av. Corrientes 1234","ciudad":"Buenos Aires","codigo_postal":"1043"}'
  # Esperado: 201 Created con es_predeterminada=true
  ```
- [ ] 9.9 Verificar en BD:
  ```bash
  docker exec -it foodstore-postgres psql -U postgres -d foodstore_db \
    -c "SELECT id, alias, es_predeterminada, eliminado_en FROM direcciones_entrega;"
  ```

---

## Checklist Final Pre-Commit

- [ ] `es_predeterminada` — nombre de campo confirmado y consistente en toda la implementación
- [ ] `get_current_user` importado de `core.dependencies` en el router
- [ ] `response_model` explícito en los 6 endpoints del router
- [ ] Ningún `session.commit()` en `service.py`
- [ ] Soft delete con `eliminado_en` — sin hard delete
- [ ] Tests escritos con pytest (NO unittest.TestCase directo)
- [ ] Coverage ≥ 60%
- [ ] Migración con `down_revision` correcto
- [ ] Conventional Commit: `feat: implement addresses-crud-by-user CRUD endpoints`
