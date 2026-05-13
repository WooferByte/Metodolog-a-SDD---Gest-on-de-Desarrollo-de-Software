## 0. Skills

- [x] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — arquitectura Router→Service→UoW→Repository→Model
- [x] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — partial index en migración
- [x] 0.3 Leer `.agents/skills/api-design/SKILL.md` — status codes, RFC 7807, endpoint naming
- [x] 0.4 Leer `.agents/skills/post-change-verification/SKILL.md` — verificación post-apply

## 1. Leer archivos existentes antes de modificar

- [x] 1.1 Leer `backend/core/models.py` — campos reales de Producto (precio_base, stock_cantidad, disponible, eliminado_en)
- [x] 1.2 Leer `backend/infrastructure/uow.py` — ver propiedad `productos` actual (BaseRepository[Producto])
- [x] 1.3 Leer `backend/productos/schemas.py` — confirmar ProductoCreate, ProductoUpdate, ProductoResponse ya existen
- [x] 1.4 Leer `backend/ingredientes/repository.py` — patrón de CustomRepository a replicar
- [x] 1.5 Leer `backend/main.py` — ver dónde agregar el nuevo router
- [x] 1.6 Leer `backend/alembic/versions/007_add_ingredientes_index.py` — patrón de migración a replicar

## 2. ProductoRepository

- [x] 2.1 Crear `backend/productos/repository.py` con `ProductoRepository(BaseRepository[Producto])`
- [x] 2.2 Implementar `list_active(skip, limit, incluir_eliminados=False)` usando ORM select + where (NO raw SQL con mappings)
- [x] 2.3 Verificar que `ProductoRepository.__init__` llama `super().__init__(session, Producto)`

## 3. ProductoService

- [x] 3.1 Crear `backend/productos/service.py` con función helper `_get_or_404(uow, producto_id)`
- [x] 3.2 Implementar `list_productos(uow, skip, limit, incluir_eliminados, current_user)` — si incluir_eliminados=True y user no tiene STOCK/ADMIN → raise HTTPException 403
- [x] 3.3 Implementar `get_producto_by_id(uow, producto_id)` → 404 si no existe
- [x] 3.4 Implementar `create_producto(uow, data)` → crea Producto desde ProductoCreate
- [x] 3.5 Implementar `update_producto(uow, producto_id, data)` → actualiza campos no-None
- [x] 3.6 Implementar `delete_producto(uow, producto_id)` → soft delete vía `uow.productos.soft_delete(producto_id)`
- [x] 3.7 Implementar `patch_stock(uow, producto_id, stock_cantidad)` → actualiza solo stock_cantidad

## 4. ProductoRouter

- [x] 4.1 Crear `backend/productos/router.py` con `APIRouter(prefix="/productos", tags=["Productos"])`
- [x] 4.2 Implementar `GET /` con `response_model=list[ProductoResponse]` — acepta `skip`, `limit`, `incluir_eliminados` (opcional); `current_user` opcional vía `get_optional_user`
- [x] 4.3 Implementar `GET /{producto_id}` con `response_model=ProductoResponse`
- [x] 4.4 Implementar `POST /` con `response_model=ProductoResponse`, `status_code=201`, `Depends(require_role(["STOCK", "ADMIN"]))`
- [x] 4.5 Implementar `PUT /{producto_id}` con `response_model=ProductoResponse`, `Depends(require_role(["STOCK", "ADMIN"]))`
- [x] 4.6 Implementar `DELETE /{producto_id}` con `response_model=None`, `status_code=204`, `Depends(require_role(["STOCK", "ADMIN"]))`
- [x] 4.7 Implementar `PATCH /{producto_id}/stock` con `response_model=ProductoResponse`, `Depends(require_role(["STOCK", "ADMIN"]))`
- [x] 4.8 Verificar que TODOS los endpoints tienen `response_model` explícito

## 5. Actualizar UnitOfWork

- [x] 5.1 Editar `backend/infrastructure/uow.py` — agregar `from productos.repository import ProductoRepository`
- [x] 5.2 Reemplazar la propiedad `productos` para instanciar `ProductoRepository(self.session)` en lugar de `BaseRepository(self.session, Producto)`
- [x] 5.3 Cambiar el type hint de la propiedad `productos` a `-> ProductoRepository`

## 6. Registrar router en main.py

- [x] 6.1 Editar `backend/main.py` — agregar `from productos.router import router as productos_router`
- [x] 6.2 Agregar `app.include_router(productos_router, prefix="/api/v1")` junto a los otros routers
- [x] 6.3 Verificar con `backend/.venv/Scripts/python -c "from main import app; print('OK')"` — DEBE imprimir OK sin errores

## 7. Migración Alembic

- [x] 7.1 Crear `backend/alembic/versions/008_add_productos_index.py` con `revision = "008_add_productos_index"`, `down_revision = "007_add_ingredientes_index"`
- [x] 7.2 `upgrade()`: `CREATE INDEX IF NOT EXISTS idx_productos_nombre_active ON productos (nombre) WHERE eliminado_en IS NULL`
- [x] 7.3 `downgrade()`: `DROP INDEX IF EXISTS idx_productos_nombre_active`

## 8. Schemas — verificar y completar si falta

- [x] 8.1 Verificar que `backend/productos/schemas.py` tiene `ProductoStockUpdate` con `stock_cantidad: int = Field(ge=0)` — si no existe, agregarlo

## 9. Tests

- [x] 9.1 Crear `backend/tests/test_productos.py` siguiendo el patrón de `test_categorias.py`
- [x] 9.2 Helper `_make_producto(id, nombre, precio_base, stock_cantidad, disponible)` retorna MagicMock
- [x] 9.3 Helper `_make_uow(repo)` con soporte async context manager
- [x] 9.4 Test: `list_productos` retorna lista de repos con `incluir_eliminados=False`
- [x] 9.5 Test: `list_productos` con `incluir_eliminados=True` y usuario sin rol → 403
- [x] 9.6 Test: `get_producto_by_id` → 404 cuando repo retorna None
- [x] 9.7 Test: `get_producto_by_id` → retorna producto cuando existe
- [x] 9.8 Test: `create_producto` → llama repo.create y retorna el producto
- [x] 9.9 Test: `update_producto` → 404 cuando no existe; actualiza campos cuando existe
- [x] 9.10 Test: `delete_producto` → 404 cuando no existe; llama soft_delete cuando existe
- [x] 9.11 Test: `patch_stock` → actualiza stock_cantidad; 404 cuando no existe
- [x] 9.12 Router integration test: `GET /api/v1/productos/` → 200 sin autenticación
- [x] 9.13 Router integration test: `POST /api/v1/productos/` sin token → 401
- [x] 9.14 Router integration test: `POST /api/v1/productos/` con CLIENT → 403

## 10. Verificación post-apply

- [x] 10.1 Ejecutar `backend/.venv/Scripts/python -c "from main import app; print('OK')"` → debe imprimir OK
- [x] 10.2 Ejecutar `backend/.venv/Scripts/pytest backend/tests/ -x -q` — todos los tests deben pasar
- [x] 10.3 Confirmar que la migración 008 está en la cadena: `backend/.venv/Scripts/alembic history`

## LECCIONES DE BUGS — OBLIGATORIO

> ⚠️ Estas reglas son obligatorias y deben verificarse antes de terminar:
>
> 1. **Router en main.py**: confirmar que `from productos.router import router as productos_router` y `app.include_router(productos_router, prefix="/api/v1")` están presentes ✅
> 2. **UoW usa ProductoRepository**: confirmar que `uow.productos` devuelve `ProductoRepository`, NO `BaseRepository(self.session, Producto)` ✅
> 3. **ORM queries**: confirmar que `list_active` usa `select(Producto).where(...)` — NO `text(...)` con `.mappings()` ✅
> 4. **Import check**: `python -c "from main import app; print('OK')"` debe pasar sin ImportError ✅
