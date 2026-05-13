## 0. Skills

- [ ] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — arquitectura Router→Service→UoW→Repository, patrones DDD, inyección de dependencias FastAPI
- [ ] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — optimización queries PostgreSQL, índices, evitar N+1, ILIKE performante
- [ ] 0.3 Leer `.agents/skills/api-design/SKILL.md` — paginación offset, formato de respuesta paginada, query params, status codes

## 1. Schemas — PaginatedProductosResponse

- [ ] 1.1 En `backend/productos/schemas.py`, agregar clase `PaginatedProductosResponse(BaseModel)` con campos: `items: List[ProductoResponse]`, `total: int`, `page: int`, `size: int`, `pages: int`

## 2. Repository — unificar list_active y agregar count

- [ ] 2.1 En `backend/productos/repository.py`, refactorizar `list_active` para aceptar parámetros adicionales: `q: Optional[str] = None`, `categoria_id: Optional[int] = None`. El método debe aplicar: `WHERE disponible = true AND eliminado_en IS NULL` en modo público (sin `incluir_eliminados`), ILIKE en `nombre` y `descripcion` si `q` es no-nulo, JOIN con `ProductoCategoria` + DISTINCT si `categoria_id` es no-nulo.
- [ ] 2.2 En `backend/productos/repository.py`, agregar método `count_active(self, incluir_eliminados: bool, q: Optional[str], categoria_id: Optional[int], alergeno_ids: list[int]) -> int` que ejecuta `SELECT COUNT(DISTINCT p.id) ...` con las mismas cláusulas WHERE que `list_active` (sin OFFSET/LIMIT).
- [ ] 2.3 En `backend/productos/repository.py`, actualizar `list_active_excluding_alergenos` para aceptar los mismos `q` y `categoria_id` params, o fusionar su lógica en `list_active` unificado (decision D-04 del design). Eliminar el método separado si se unifica.
- [ ] 2.4 Verificar que el import de `or_` de sqlalchemy esté presente en `repository.py` (necesario para ILIKE en `nombre` OR `descripcion`).
- [ ] 2.5 Verificar que el import de `ProductoCategoria` ya esté presente en `repository.py` (necesario para el JOIN de categoria_id).

## 3. Service — propagar nuevos parámetros

- [ ] 3.1 En `backend/productos/service.py`, actualizar la firma de `list_productos` para aceptar `q: Optional[str] = None` y `categoria_id: Optional[int] = None`.
- [ ] 3.2 En `backend/productos/service.py`, actualizar el cuerpo de `list_productos` para llamar al método unificado `uow.productos.list_active(...)` con todos los parámetros (`skip`/`limit`, `incluir_eliminados`, `excluir_alergenos`, `q`, `categoria_id`).
- [ ] 3.3 En `backend/productos/service.py`, agregar llamada a `uow.productos.count_active(...)` con los mismos filtros (sin skip/limit) para obtener `total`.
- [ ] 3.4 En `backend/productos/service.py`, cambiar el tipo de retorno de `list_productos` de `list[Producto]` a `PaginatedProductosResponse`, construyendo la respuesta con `items`, `total`, `page`, `size`, `pages`.
- [ ] 3.5 Agregar import de `PaginatedProductosResponse` en `service.py`.

## 4. Router — nuevos query params y response_model actualizado

- [ ] 4.1 En `backend/productos/router.py`, agregar query params al endpoint `GET /`: `q: Optional[str] = Query(default=None, max_length=200)` y `categoria_id: Optional[int] = Query(default=None, ge=1)`.
- [ ] 4.2 En `backend/productos/router.py`, agregar query params de paginación canónicos: `page: int = Query(default=1, ge=1)` y `size: int = Query(default=20, ge=1, le=100)`. Computar `skip = (page - 1) * size` y `limit = size` para mantener compatibilidad con la capa de servicio.
- [ ] 4.3 En `backend/productos/router.py`, actualizar `response_model` del endpoint `GET /` de `list[ProductoResponse]` a `PaginatedProductosResponse`.
- [ ] 4.4 En `backend/productos/router.py`, pasar `q` y `categoria_id` al llamado de `service.list_productos(...)`.
- [ ] 4.5 En `backend/productos/router.py`, actualizar el tipo de retorno de `list_productos` de `list[ProductoResponse]` a `PaginatedProductosResponse`.
- [ ] 4.6 Agregar import de `PaginatedProductosResponse` en `router.py`.

## 5. Tests — actualizar tests existentes

- [ ] 5.1 En `backend/tests/test_productos.py`, actualizar todos los asserts sobre la respuesta del `GET /api/v1/productos` que esperaban una lista plana: ahora deben esperar `response.json()["items"]` y verificar `response.json()["total"]`, `response.json()["page"]`, `response.json()["size"]`, `response.json()["pages"]`.
- [ ] 5.2 En `backend/tests/test_productos.py`, actualizar los mocks del servicio/repositorio que retornaban `list[Producto]` para retornar un `PaginatedProductosResponse` (o mock equivalente con los campos del envelope).

## 6. Tests — nuevos casos para búsqueda y filtros

- [ ] 6.1 Agregar test de servicio: `list_productos` con `q="pizza"` invoca el repositorio con ese parámetro y retorna solo productos cuyo nombre/descripción contiene "pizza".
- [ ] 6.2 Agregar test de servicio: `list_productos` con `q="xyznonexistent"` retorna `PaginatedProductosResponse` con `items=[]` y `total=0`.
- [ ] 6.3 Agregar test de servicio: `list_productos` con `categoria_id=3` invoca el repositorio con ese parámetro y retorna solo productos de esa categoría.
- [ ] 6.4 Agregar test de servicio: `list_productos` con `q="pizza"` y `categoria_id=2` aplica ambos filtros simultáneamente.
- [ ] 6.5 Agregar test de router (integración): `GET /api/v1/productos?q=test` retorna 200 con respuesta en forma de envelope `{ items, total, page, size, pages }`.
- [ ] 6.6 Agregar test de router (integración): `GET /api/v1/productos?categoria_id=abc` retorna 422.
- [ ] 6.7 Agregar test de servicio: `list_productos` sin autenticación retorna solo productos con `disponible=true` (RN-CA08).
- [ ] 6.8 Agregar test de repositorio: `list_active(q="pizza")` construye la query con ILIKE y retorna resultados correctos (mock de session).
- [ ] 6.9 Agregar test de repositorio: `list_active(categoria_id=3)` construye la query con JOIN en `ProductoCategoria` (mock de session).
- [ ] 6.10 Agregar test de repositorio: `count_active(...)` retorna el conteo correcto para los filtros dados.

## 7. Verificación final

- [ ] 7.1 Ejecutar `pytest backend/tests/test_productos.py -v` — todos los tests deben pasar (sin regresiones).
- [ ] 7.2 Ejecutar `pytest backend/tests/ -v` — suite completa verde.
- [ ] 7.3 Ejecutar `black --check backend/productos/` y `flake8 backend/productos/` — sin errores de formato.
- [ ] 7.4 Verificar manualmente en Swagger (`http://localhost:8000/docs`): `GET /api/v1/productos?q=pizza` retorna envelope paginado. `GET /api/v1/productos?categoria_id=1` retorna solo productos de esa categoría. `GET /api/v1/productos?page=1&size=5` retorna 5 items con metadatos correctos.
