## 0. Skills

- [x] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — patrones FastAPI DDD, router/service/uow/repository, Pydantic v2
- [x] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — índices parciales, queries parametrizadas, migraciones Alembic
- [x] 0.3 Leer `.agents/skills/api-design/SKILL.md` — status codes, filtros query params, response_model, auth guards
- [x] 0.4 Leer `.agents/skills/post-change-verification/SKILL.md` — criterios de aprobación, pytest, alembic, comandos de verificación

## 1. Leer archivos existentes antes de modificar

- [x] 1.1 Leer `backend/core/models.py` — confirmar campos de `Ingrediente` (nombre, es_alergeno, eliminado_en)
- [x] 1.2 Leer `backend/ingredientes/schemas.py` — confirmar `IngredienteCreate`, `IngredienteUpdate`, `IngredienteResponse` ya existen
- [x] 1.3 Leer `backend/infrastructure/uow.py` — ver cómo está wired `uow.ingredientes` actualmente
- [x] 1.4 Leer `backend/infrastructure/repositories/base_repository.py` — interfaz de `BaseRepository[T]`
- [x] 1.5 Leer `backend/categorias/repository.py` — referencia para `IngredienteRepository`
- [x] 1.6 Leer `backend/categorias/service.py` — referencia para `IngredienteService`
- [x] 1.7 Leer `backend/categorias/router.py` — referencia para `IngredienteRouter`
- [x] 1.8 Leer `backend/alembic/versions/006_add_categoria_padre_id_index.py` — obtener `down_revision` para encadenar migración 007
- [x] 1.9 Leer `backend/main.py` — ver dónde registrar el nuevo router
- [x] 1.10 Leer `backend/tests/test_categorias.py` — convenciones de tests (mocks, estructura, pytest.mark.asyncio)

## 2. Repository

- [x] 2.1 Crear `backend/ingredientes/repository.py` con clase `IngredienteRepository(BaseRepository[Ingrediente])`
- [x] 2.2 Implementar `has_active_products(ingrediente_id: int) -> bool` — EXISTS query en `producto_ingrediente JOIN productos WHERE eliminado_en IS NULL LIMIT 1`
- [x] 2.3 Implementar `list_by_alergeno(es_alergeno: bool, skip: int, limit: int) -> list[Ingrediente]` — query con filtro `es_alergeno = :val` y soft-delete exclusion, ORDER BY nombre

## 3. Service

- [x] 3.1 Crear `backend/ingredientes/service.py` con todas las funciones del service
- [x] 3.2 Implementar `list_ingredientes(uow, skip, limit, es_alergeno=None)` — delega a `list_all` o `list_by_alergeno` según parámetro
- [x] 3.3 Implementar `get_ingrediente_by_id(uow, ingrediente_id)` — 404 si no existe
- [x] 3.4 Implementar `create_ingrediente(uow, data)` — `IntegrityError` → 409
- [x] 3.5 Implementar `update_ingrediente(uow, ingrediente_id, data)` — 404 guard + partial update + `IntegrityError` → 409
- [x] 3.6 Implementar `delete_ingrediente(uow, ingrediente_id)` — 404 guard + `has_active_products` guard (409) + `soft_delete`

## 4. Router

- [x] 4.1 Crear `backend/ingredientes/router.py` con `APIRouter(prefix="/ingredientes", tags=["Ingredientes"])`
- [x] 4.2 Implementar `GET /` — público, `response_model=list[IngredienteResponse]`, parámetros `skip`, `limit`, `es_alergeno: Optional[bool] = None`
- [x] 4.3 Implementar `GET /{ingrediente_id}` — público, `response_model=IngredienteResponse`
- [x] 4.4 Implementar `POST /` — `require_role(["STOCK", "ADMIN"])`, `response_model=IngredienteResponse`, `status_code=201`
- [x] 4.5 Implementar `PUT /{ingrediente_id}` — `require_role(["STOCK", "ADMIN"])`, `response_model=IngredienteResponse`, `status_code=200`
- [x] 4.6 Implementar `DELETE /{ingrediente_id}` — `require_role(["STOCK", "ADMIN"])`, `response_model=None`, `status_code=204`, retorna `Response(status_code=204)`
- [x] 4.7 Verificar que TODOS los endpoints tienen `response_model` explícito

## 5. UoW e infraestructura

- [x] 5.1 Actualizar `backend/infrastructure/uow.py`: importar `IngredienteRepository` y cambiar el property `ingredientes` para retornar `IngredienteRepository` en lugar de `BaseRepository[Ingrediente]`
- [x] 5.2 Añadir `__init__.py` a `backend/ingredientes/` si no existe

## 6. Registrar router en main.py

- [x] 6.1 Editar `backend/main.py`: importar `ingredientes.router` e incluirlo con `app.include_router(ingredientes_router, prefix="/api/v1")`

## 7. Migración Alembic

- [x] 7.1 Crear `backend/alembic/versions/007_add_ingredientes_index.py` con `down_revision = "006_add_categoria_padre_id_index"`
- [x] 7.2 Implementar `upgrade()`: `CREATE INDEX IF NOT EXISTS idx_ingredientes_nombre_active ON ingredientes (nombre) WHERE eliminado_en IS NULL`
- [x] 7.3 Implementar `downgrade()`: `DROP INDEX IF EXISTS idx_ingredientes_nombre_active`

## 8. Tests

- [x] 8.1 Crear `backend/tests/test_ingredientes.py`
- [x] 8.2 Test `TestListIngredientes`: service retorna lista del repo (con y sin filtro `es_alergeno`)
- [x] 8.3 Test `TestGetIngredienteById`: 404 cuando no existe, retorna ingrediente cuando existe
- [x] 8.4 Test `TestCreateIngrediente`: creación exitosa, `IntegrityError` → 409
- [x] 8.5 Test `TestUpdateIngrediente`: actualización exitosa, 404 para ID inexistente, `IntegrityError` → 409
- [x] 8.6 Test `TestDeleteIngrediente`: soft-delete exitoso, bloqueado por productos activos (409), 404 para ID inexistente
- [x] 8.7 Test `TestGetIngredientesPublic`: `GET /api/v1/ingredientes/` → 200 sin Authorization
- [x] 8.8 Test `TestPostIngredienteRequiresAuth`: `POST /api/v1/ingredientes/` sin token → 401, con CLIENT → 403
- [x] 8.9 Test `TestDeleteIngredienteRequiresAuth`: `DELETE /api/v1/ingredientes/{id}` sin token → 401
- [x] 8.10 Test `TestPutIngredienteRequiresAuth`: `PUT /api/v1/ingredientes/{id}` sin token → 401

## 9. Verificación

- [x] 9.1 Ejecutar `backend/.venv/Scripts/alembic upgrade head` — debe terminar sin error
- [x] 9.2 Ejecutar `backend/.venv/Scripts/pytest tests/ -x -q` — todos los tests deben pasar
- [x] 9.3 Verificar cobertura ≥ 60% en el módulo `ingredientes/`
