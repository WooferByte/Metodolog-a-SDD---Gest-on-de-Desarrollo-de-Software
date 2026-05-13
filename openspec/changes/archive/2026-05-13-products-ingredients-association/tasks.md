## 0. Skills

- [ ] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — arquitectura Router→Service→UoW→Repository→Model, patrones DDD, reglas de capas
- [ ] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — queries ORM sobre pivot tables, índices, subqueries para excluirAlergenos
- [ ] 0.3 Leer `.agents/skills/api-design/SKILL.md` — sub-recursos REST, status codes, query params, validación

## 1. Schemas (`productos/schemas.py`)

- [ ] 1.1 Agregar clase `IngredienteAsociacion(BaseModel)` con campos `ingrediente_id: int` y `es_removible: bool = False`
- [ ] 1.2 Agregar clase `IngredienteCompacto(BaseModel)` con campos `id: int`, `nombre: str`, `es_alergeno: bool`, `es_removible: bool` y `model_config = {"from_attributes": True}`
- [ ] 1.3 Agregar clase `ProductoIngredienteSetRequest(BaseModel)` con campo `ingredientes: List[IngredienteAsociacion] = []`
- [ ] 1.4 Agregar campo `ingredientes: List[IngredienteCompacto] = []` a `ProductoResponse`

## 2. Repository (`productos/repository.py`)

- [ ] 2.1 Agregar clase `ProductoIngredienteRepository` (no hereda `BaseRepository` — maneja pivot directamente, igual que `ProductoCategoriaRepository`)
- [ ] 2.2 Implementar método `get_ingredientes(producto_id) -> list[tuple[Ingrediente, bool]]` — SELECT JOIN ingredientes ON producto_ingrediente, retorna pares (ingrediente, es_removible), ordena por nombre
- [ ] 2.3 Implementar método `set_ingredientes(producto_id, items: list[dict]) -> None` — DELETE all existing rows, INSERT new set atómicamente en la misma transacción, flush entre ambas operaciones
- [ ] 2.4 Implementar método `get_association(producto_id, ingrediente_id) -> ProductoIngrediente | None` — busca fila pivote exacta
- [ ] 2.5 Implementar método `remove_ingrediente(producto_id, ingrediente_id) -> None` — DELETE fila pivote exacta, flush
- [ ] 2.6 Implementar método `list_active_excluding_alergenos(skip, limit, alergeno_ids: list[int]) -> list[Producto]` — SELECT productos WHERE eliminado_en IS NULL AND id NOT IN (SELECT producto_id FROM producto_ingrediente WHERE ingrediente_id = ANY(:ids)), ORDER BY nombre, LIMIT/OFFSET

## 3. UoW (`infrastructure/uow.py`)

- [ ] 3.1 Importar `ProductoIngredienteRepository` desde `productos.repository`
- [ ] 3.2 Reemplazar la propiedad `producto_ingredientes` para que instancie `ProductoIngredienteRepository(self.session)` en lugar de `BaseRepository(self.session, ProductoIngrediente)`
- [ ] 3.3 Actualizar type hint del property a `ProductoIngredienteRepository`

## 4. Service (`productos/service.py`)

- [ ] 4.1 Agregar función helper `_ingredientes_to_compacto(pairs: list[tuple[Ingrediente, bool]]) -> list[IngredienteCompacto]` — mapea (ingrediente, es_removible) a `IngredienteCompacto`
- [ ] 4.2 Actualizar `get_producto_by_id` — llamar `uow.producto_ingredientes.get_ingredientes(producto_id)` y poblar `ingredientes` en `ProductoResponse`
- [ ] 4.3 Agregar función `list_ingredientes_producto(uow, producto_id) -> list[IngredienteCompacto]` — valida producto existe (_get_or_404), llama repo, mapea a compacto
- [ ] 4.4 Agregar función `set_ingredientes_producto(uow, producto_id, data: ProductoIngredienteSetRequest) -> list[IngredienteCompacto]` — valida producto, valida cada ingrediente_id existe y no está eliminado (404 si no), llama `uow.producto_ingredientes.set_ingredientes`, retorna lista actualizada
- [ ] 4.5 Agregar función `remove_ingrediente_producto(uow, producto_id, ingrediente_id) -> None` — valida producto (_get_or_404), busca asociación (404 si no existe), llama `uow.producto_ingredientes.remove_ingrediente`
- [ ] 4.6 Actualizar `list_productos` para aceptar `excluir_alergenos: list[int] = []` — si la lista no está vacía, delega a `uow.producto_ingredientes.list_active_excluding_alergenos`; caso contrario mantiene comportamiento actual

## 5. Router (`productos/router.py`)

- [ ] 5.1 Importar los nuevos schemas: `IngredienteCompacto`, `ProductoIngredienteSetRequest`
- [ ] 5.2 Agregar endpoint `GET /{producto_id}/ingredientes` — `response_model=list[IngredienteCompacto]`, público, llama `service.list_ingredientes_producto`; declarado ANTES de `/{producto_id}`
- [ ] 5.3 Agregar endpoint `PUT /{producto_id}/ingredientes` — `response_model=list[IngredienteCompacto]`, `status_code=200`, requiere STOCK o ADMIN, llama `service.set_ingredientes_producto`; declarado ANTES de `/{producto_id}`
- [ ] 5.4 Agregar endpoint `DELETE /{producto_id}/ingredientes/{ingrediente_id}` — `response_model=None`, `status_code=204`, requiere STOCK o ADMIN, llama `service.remove_ingrediente_producto`; declarado ANTES de `/{producto_id}`
- [ ] 5.5 Actualizar `list_productos` endpoint — agregar query param `excluir_alergenos: Optional[str] = None` (recibe como string "1,3,7"), parsear a `list[int]` en router, validar que todos sean enteros y no más de 50 (422 si no), pasar al service
- [ ] 5.6 Actualizar docstring del router con los 3 nuevos endpoints en la cabecera

## 6. Tests (`backend/tests/test_productos_ingredientes.py`)

- [ ] 6.1 Crear archivo `test_productos_ingredientes.py` con helpers `_make_producto`, `_make_ingrediente`, `_make_pivot` (MagicMock)
- [ ] 6.2 Tests de servicio — `list_ingredientes_producto`: producto no existe → 404; producto sin ingredientes → []; producto con ingredientes → lista correcta con es_removible
- [ ] 6.3 Tests de servicio — `set_ingredientes_producto`: producto no existe → 404; ingrediente_id inválido → 404; lista vacía → []; reemplazo válido → lista actualizada
- [ ] 6.4 Tests de servicio — `remove_ingrediente_producto`: producto no existe → 404; asociación no existe → 404; asociación válida → None (sin error)
- [ ] 6.5 Tests de router — `GET /{id}/ingredientes`: 200 con lista; 404 producto no existe
- [ ] 6.6 Tests de router — `PUT /{id}/ingredientes`: 200 con lista; 401 sin token; 403 con rol CLIENT
- [ ] 6.7 Tests de router — `DELETE /{id}/ingredientes/{ing_id}`: 204 asociación válida; 404 asociación no existe; 401 sin token; 403 con rol CLIENT
- [ ] 6.8 Tests de router — `GET /` con `?excluirAlergenos`: sin parámetro → lista completa; con IDs válidos → lista filtrada; con valor no-entero → 422; con más de 50 IDs → 422
- [ ] 6.9 Test de servicio — `get_producto_by_id` enriquecido: respuesta incluye campo `ingredientes` con valores correctos de es_removible

## 7. Verificación final

- [ ] 7.1 Ejecutar `pytest backend/tests/test_productos_ingredientes.py -v` — todos los tests pasan
- [ ] 7.2 Ejecutar `pytest backend/ --cov=productos --cov-report=term-missing` — coverage ≥ 60%
- [ ] 7.3 Ejecutar `black --check backend/` y `flake8 backend/` — sin errores de estilo
- [ ] 7.4 Verificar en Swagger (`http://localhost:8000/docs`) que los 3 nuevos endpoints aparecen bajo tag "Productos"
- [ ] 7.5 Verificar que `GET /api/v1/productos/{id}` retorna campo `ingredientes` en la respuesta
- [ ] 7.6 Verificar que `GET /api/v1/productos/?excluirAlergenos=X` filtra correctamente usando psql o Swagger
