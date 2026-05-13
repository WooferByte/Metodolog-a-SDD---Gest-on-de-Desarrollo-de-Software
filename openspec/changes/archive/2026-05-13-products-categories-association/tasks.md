## 0. Skills

- [ ] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — patrones FastAPI DDD: Router → Service → UoW → Repository → Model
- [ ] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — queries sobre tabla pivote, índices, operaciones bulk
- [ ] 0.3 Leer `.agents/skills/api-design/SKILL.md` — endpoints REST para sub-recursos y asociaciones N:M

## 1. Schemas (backend/productos/schemas.py)

- [ ] 1.1 Agregar `CategoriaCompacta` schema con campos `id: int`, `nombre: str`, `padre_id: Optional[int]`
- [ ] 1.2 Agregar `ProductoCategoriaSetRequest` schema con campo `categoria_ids: list[int]` y validación `@field_validator` que acepta lista vacía
- [ ] 1.3 Modificar `ProductoResponse` para agregar campo `categorias: list[CategoriaCompacta] = []`

## 2. Repository (backend/productos/repository.py)

- [ ] 2.1 Agregar clase `ProductoCategoriaRepository` (hereda de `BaseRepository[ProductoCategoria]` o usa sesión directamente)
- [ ] 2.2 Implementar método `get_categorias(producto_id: int) -> list[Categoria]` — SELECT con JOIN a tabla `categorias`, filtra `categorias.eliminado_en IS NULL`
- [ ] 2.3 Implementar método `set_categorias(producto_id: int, categoria_ids: list[int]) -> None` — DELETE all existing rows for producto_id + INSERT new rows, dentro de la misma sesión UoW
- [ ] 2.4 Implementar método `get_association(producto_id: int, categoria_id: int) -> ProductoCategoria | None` — SELECT fila específica del pivote
- [ ] 2.5 Implementar método `remove_categoria(producto_id: int, categoria_id: int) -> None` — DELETE fila específica del pivote

## 3. UoW Registration (backend/infrastructure/uow.py)

- [ ] 3.1 Importar `ProductoCategoriaRepository` desde `productos.repository`
- [ ] 3.2 Agregar atributo `producto_categorias: ProductoCategoriaRepository` al `UnitOfWork` y asignarlo en `__aenter__`

## 4. Service (backend/productos/service.py)

- [ ] 4.1 Implementar `list_categorias_producto(uow, producto_id: int) -> list[CategoriaCompacta]` — verifica que el producto existe y no está soft-deleted; retorna categorías asociadas
- [ ] 4.2 Implementar `set_categorias_producto(uow, producto_id: int, categoria_ids: list[int]) -> list[CategoriaCompacta]` — verifica producto; para cada categoria_id verifica existencia y no soft-deleted vía `uow.categorias.get_by_id()`; llama `uow.producto_categorias.set_categorias()`; retorna lista actualizada
- [ ] 4.3 Implementar `remove_categoria_producto(uow, producto_id: int, categoria_id: int) -> None` — verifica producto existe; verifica asociación existe (`get_association`); llama `remove_categoria()`; lanza 404 si no existe la asociación
- [ ] 4.4 Modificar `get_producto_by_id(uow, producto_id: int)` para que incluya `categorias` en el `ProductoResponse` devuelto (cargar con `get_categorias(producto_id)` y mapear a `CategoriaCompacta`)

## 5. Router (backend/productos/router.py)

- [ ] 5.1 Agregar endpoint `GET /{producto_id}/categorias` — público (sin auth), `response_model=list[CategoriaCompacta]`, llama `service.list_categorias_producto()`
- [ ] 5.2 Agregar endpoint `PUT /{producto_id}/categorias` — requiere ADMIN o STOCK, `response_model=list[CategoriaCompacta]`, body `ProductoCategoriaSetRequest`, llama `service.set_categorias_producto()`, retorna HTTP 200
- [ ] 5.3 Agregar endpoint `DELETE /{producto_id}/categorias/{categoria_id}` — requiere ADMIN o STOCK, `response_model=None`, `status_code=204`, llama `service.remove_categoria_producto()`
- [ ] 5.4 Verificar orden de declaración de rutas: los nuevos endpoints con path `/{producto_id}/categorias` deben declararse ANTES de `/{producto_id}` para evitar conflictos de matching en FastAPI

## 6. Tests (backend/tests/test_productos_categorias.py)

- [ ] 6.1 Crear `backend/tests/test_productos_categorias.py` con fixture de producto y categorías de prueba
- [ ] 6.2 Test `GET /api/v1/productos/{id}/categorias` — producto sin categorías retorna `[]`
- [ ] 6.3 Test `GET /api/v1/productos/{id}/categorias` — producto con categorías retorna lista correcta
- [ ] 6.4 Test `GET /api/v1/productos/{id}/categorias` — producto no existe retorna 404
- [ ] 6.5 Test `PUT /api/v1/productos/{id}/categorias` — reemplaza categorías correctamente con token ADMIN
- [ ] 6.6 Test `PUT /api/v1/productos/{id}/categorias` — body vacío `[]` elimina todas las asociaciones
- [ ] 6.7 Test `PUT /api/v1/productos/{id}/categorias` — categoria_id inexistente retorna 404
- [ ] 6.8 Test `PUT /api/v1/productos/{id}/categorias` — sin auth retorna 401
- [ ] 6.9 Test `PUT /api/v1/productos/{id}/categorias` — rol CLIENT retorna 403
- [ ] 6.10 Test `DELETE /api/v1/productos/{id}/categorias/{cat_id}` — elimina asociación existente, retorna 204
- [ ] 6.11 Test `DELETE /api/v1/productos/{id}/categorias/{cat_id}` — asociación no existe retorna 404
- [ ] 6.12 Test `DELETE /api/v1/productos/{id}/categorias/{cat_id}` — sin auth retorna 401
- [ ] 6.13 Test `GET /api/v1/productos/{id}` — response incluye campo `categorias` (lista, puede ser vacía)

## 7. Verification

- [ ] 7.1 Ejecutar `pytest backend/tests/test_productos_categorias.py -v` — todos los tests pasan
- [ ] 7.2 Ejecutar `pytest backend/tests/ --cov=productos --cov-report=term-missing` — cobertura del módulo productos ≥ 60%
- [ ] 7.3 Ejecutar `black --check backend/productos/` y `flake8 backend/productos/` — sin errores de estilo
- [ ] 7.4 Verificar en Swagger (`http://localhost:8000/docs`) que los 3 nuevos endpoints aparecen bajo el tag "Productos"
- [ ] 7.5 Verificar que `GET /api/v1/productos/{id}` retorna campo `categorias` en la respuesta
