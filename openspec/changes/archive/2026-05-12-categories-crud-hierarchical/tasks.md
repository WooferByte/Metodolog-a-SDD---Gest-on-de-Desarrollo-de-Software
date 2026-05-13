## 0. Skills

- [x] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — patrones DDD: Router → Service → UoW → Repository, HTTPException en service, response_model explícito
- [x] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — CTE recursivo, índice parcial en padre_id, queries parametrizadas
- [x] 0.3 Leer `.agents/skills/api-design/SKILL.md` — status codes (201, 204, 400, 404, 409), endpoint naming, pagination
- [x] 0.4 Leer `.agents/skills/post-change-verification/SKILL.md` — checklist de verificación pre-archive: pytest, alembic, uvicorn

## 1. Repository

- [x] 1.1 Crear `backend/categorias/repository.py` con clase `CategoriaRepository(BaseRepository[Categoria])` que hereda todos los métodos genéricos de `BaseRepository`
- [x] 1.2 Implementar método `get_tree(root_id: Optional[int] = None) -> list[dict]` usando `sqlalchemy.text()` con CTE recursivo PostgreSQL; retornar filas con `id, nombre, descripcion, padre_id, creado_en, actualizado_en, depth`; filtrar `eliminado_en IS NULL`
- [x] 1.3 Implementar método `has_active_products(categoria_id: int) -> bool` que ejecuta `SELECT 1 FROM producto_categoria pc JOIN productos p ON pc.producto_id = p.id WHERE pc.categoria_id = :cid AND p.eliminado_en IS NULL LIMIT 1` usando `text()`

## 2. UnitOfWork — override categorias property

- [x] 2.1 En `backend/infrastructure/uow.py`: importar `CategoriaRepository` desde `categorias.repository`
- [x] 2.2 Reemplazar el property `categorias` de `UnitOfWork` para que retorne `CategoriaRepository(self.session)` en lugar de `BaseRepository(self.session, Categoria)`; mantener el mismo caché `_repositories["categorias"]`

## 3. Schemas — completar CategoriaTreeItem

- [x] 3.1 En `backend/categorias/schemas.py`: agregar schema `CategoriaTreeItem(CategoriaResponse)` con campo `depth: int` para la respuesta de los endpoints `/tree` y `/{id}/subtree`

## 4. Service

- [x] 4.1 Crear `backend/categorias/service.py` con función `list_categorias(uow, skip, limit)` que retorna `list[Categoria]` usando `uow.categorias.list_all(skip, limit)` ordenados por `nombre`
- [x] 4.2 Implementar `get_categoria_by_id(uow, categoria_id)` — retorna `Categoria` o lanza `HTTPException(404)`
- [x] 4.3 Implementar `get_tree(uow, root_id=None)` — llama `uow.categorias.get_tree(root_id)` y retorna `list[dict]` (mapeados a `CategoriaTreeItem`)
- [x] 4.4 Implementar helper `_would_create_cycle(uow, child_id, proposed_padre_id) -> bool` — itera la cadena de ancestros de `proposed_padre_id` usando `uow.categorias.get_by_id`; usa set `visited` para guard contra ciclos existentes; retorna `True` si `child_id` aparece en la cadena
- [x] 4.5 Implementar `create_categoria(uow, data: CategoriaCreate) -> Categoria`:
  - Si `data.padre_id` is not None: verificar que el padre existe (404 si no) — no hay riesgo de ciclo en create de nueva categoría
  - Crear instancia `Categoria(**data.model_dump())`
  - Llamar `await uow.categorias.create(categoria)` dentro del contexto UoW
  - Capturar `IntegrityError` y relanzar como `HTTPException(409, "Category name already exists")`
- [x] 4.6 Implementar `update_categoria(uow, categoria_id, data: CategoriaUpdate) -> Categoria`:
  - Obtener categoría existente (404 si no existe)
  - Si `data.padre_id` cambia y no es None: llamar `_would_create_cycle(uow, categoria_id, data.padre_id)` → si True lanzar `HTTPException(400, "Cycle detected in category hierarchy")`
  - Si `data.padre_id` cambia y no es None: verificar que el nuevo padre existe (404 si no)
  - Aplicar campos del `data` al modelo (solo los que no sean None)
  - Llamar `await uow.categorias.update(categoria)`
  - Capturar `IntegrityError` y relanzar como `HTTPException(409)`
- [x] 4.7 Implementar `delete_categoria(uow, categoria_id)`:
  - Obtener categoría existente (404 si no existe)
  - Llamar `await uow.categorias.has_active_products(categoria_id)` → si True lanzar `HTTPException(409, "Cannot delete category with active products")`
  - Llamar `await uow.categorias.soft_delete(categoria_id)`

## 5. Router

- [x] 5.1 Crear `backend/categorias/router.py` con `APIRouter(prefix="/categorias", tags=["Categorias"])`
- [x] 5.2 Implementar `GET /` con `response_model=list[CategoriaResponse]`, parámetros `skip: int = 0, limit: int = 100`; sin autenticación; delegar a `list_categorias`
- [x] 5.3 Implementar `GET /tree` con `response_model=list[CategoriaTreeItem]`; sin autenticación; delegar a `get_tree(uow, root_id=None)`; IMPORTANTE: definir esta ruta ANTES de `GET /{id}` para evitar conflicto de rutas
- [x] 5.4 Implementar `GET /{categoria_id}` con `response_model=CategoriaResponse`; sin autenticación; delegar a `get_categoria_by_id`
- [x] 5.5 Implementar `GET /{categoria_id}/subtree` con `response_model=list[CategoriaTreeItem]`; sin autenticación; delegar a `get_tree(uow, root_id=categoria_id)`; lanzar 404 si root no existe antes de llamar get_tree
- [x] 5.6 Implementar `POST /` con `response_model=CategoriaResponse`, `status_code=201`; auth: `Depends(require_role(["STOCK", "ADMIN"]))`; delegar a `create_categoria`
- [x] 5.7 Implementar `PUT /{categoria_id}` con `response_model=CategoriaResponse`, `status_code=200`; auth: `Depends(require_role(["STOCK", "ADMIN"]))`; delegar a `update_categoria`
- [x] 5.8 Implementar `DELETE /{categoria_id}` con `response_model=None`, `status_code=204`; auth: `Depends(require_role(["STOCK", "ADMIN"]))`; delegar a `delete_categoria`; retornar `Response(status_code=204)` (no body)
- [x] 5.9 Agregar `__init__.py` a `backend/categorias/` si no existe para que Python reconozca el paquete

## 6. Registrar router en main.py

- [x] 6.1 En `backend/main.py`: importar `from categorias.router import router as categorias_router` y agregar `app.include_router(categorias_router, prefix="/api/v1")`

## 7. Migración Alembic

- [x] 7.1 Crear `backend/alembic/versions/006_add_categoria_padre_id_index.py` con `revision = "006_add_categoria_padre_id_index"` y `down_revision = "005_ingredientes_excluidos_integer_array"`
- [x] 7.2 Implementar `upgrade()`: ejecutar `CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_categorias_padre_id ON categorias (padre_id) WHERE eliminado_en IS NULL` — nota: `CONCURRENTLY` no está disponible en transacciones; usar `op.execute("COMMIT")` antes si es necesario, o simplemente `CREATE INDEX IF NOT EXISTS` (sin CONCURRENTLY) para ser compatible con alembic en transacción
- [x] 7.3 Implementar `downgrade()`: ejecutar `DROP INDEX IF EXISTS idx_categorias_padre_id`

## 8. Tests

- [x] 8.1 Crear `backend/tests/test_categorias.py` con fixtures de mock `AsyncMock` para `UnitOfWork` y `CategoriaRepository`
- [x] 8.2 Test `test_list_categorias_returns_active_only` — mock `uow.categorias.list_all` retornando dos categorías activas y verificar que el service retorna ambas
- [x] 8.3 Test `test_get_categoria_by_id_not_found` — mock `uow.categorias.get_by_id` retornando `None` y verificar que service lanza `HTTPException(404)`
- [x] 8.4 Test `test_create_categoria_success` — mock `uow.categorias.create` y verificar que retorna la categoría creada con `id` asignado
- [x] 8.5 Test `test_create_categoria_duplicate_name` — mock `uow.categorias.create` lanzando `IntegrityError` y verificar que service relanza `HTTPException(409)`
- [x] 8.6 Test `test_update_categoria_cycle_detection` — mock la cadena de ancestros para simular A→B→C y verificar que `update_categoria` con `padre_id=C` para categoría A lanza `HTTPException(400)`
- [x] 8.7 Test `test_update_categoria_self_cycle` — intentar `update_categoria` con `padre_id == categoria_id` y verificar `HTTPException(400)`
- [x] 8.8 Test `test_delete_categoria_blocked_by_products` — mock `uow.categorias.has_active_products` retornando `True` y verificar `HTTPException(409)`
- [x] 8.9 Test `test_delete_categoria_success` — mock `has_active_products` retornando `False` y verificar que `soft_delete` es llamado
- [x] 8.10 Test de router: `test_get_categorias_public` — verificar que `GET /api/v1/categorias` responde 200 sin token (usando `TestClient`)
- [x] 8.11 Test de router: `test_post_categoria_requires_auth` — verificar que `POST /api/v1/categorias` sin token retorna 401
- [x] 8.12 Test de router: `test_post_categoria_requires_stock_role` — verificar que `POST /api/v1/categorias` con token CLIENT retorna 403

## 9. Verificación

- [x] 9.1 Ejecutar `cd backend && .venv/Scripts/black --check .` — sin errores de formato
- [x] 9.2 Ejecutar `cd backend && .venv/Scripts/flake8 .` — sin errores de linting
- [x] 9.3 Ejecutar `cd backend && .venv/Scripts/alembic upgrade head` — migración 006 aplicada sin error
- [x] 9.4 Ejecutar `cd backend && .venv/Scripts/pytest tests/test_categorias.py -v` — todos los tests pasan
- [x] 9.5 Ejecutar `cd backend && .venv/Scripts/pytest --cov=. --cov-report=term-missing -x -q` — cobertura global ≥ 60%
- [x] 9.6 Levantar uvicorn y verificar que `GET http://localhost:8000/api/v1/categorias` retorna 200 y `POST http://localhost:8000/api/v1/categorias` sin token retorna 401
- [x] 9.7 Verificar en Swagger UI (`http://localhost:8000/docs`) que los 7 endpoints de categorías aparecen con los `response_model` correctos
