## 0. Skills

- [x] 0.1 Leer `.agents/skills/python-fastapi-ddd-skill/SKILL.md` — Router→Service→UoW→Repository, HTTPException en service, response_model explícito
- [x] 0.2 Leer `.agents/skills/supabase-postgres-best-practices/SKILL.md` — batch SELECT IN query, índices en productos.stock y productos.precio
- [x] 0.3 Leer `.agents/skills/api-design/SKILL.md` — POST endpoint, status codes 200 vs 422, RFC 7807
- [x] 0.4 Leer `.agents/skills/rest-api-design-patterns/SKILL.md` — estructura API, versionado /api/v1/
- [x] 0.5 Leer `.agents/skills/jwt-security/SKILL.md` — get_current_user(), require_role([CLIENT])
- [x] 0.6 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens semánticos OKLCH, componentes modal/alert
- [x] 0.7 Leer `.agents/skills/frontend-state-management/SKILL.md` — useMutation vs useQuery, cuándo Zustand vs TanStack Query
- [x] 0.8 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — performance hooks, evitar re-renders innecesarios
- [x] 0.9 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — auth JWT Zustand, guards de rutas, toasts HTTP

## 1. Backend — Schemas Pydantic v2

- [x] 1.1 Abrir `backend/pedidos/schemas.py` — agregar `ValidarItemRequest` (producto_id: int, cantidad: int ≥ 1, precio_carrito: Decimal)
- [x] 1.2 Agregar `ValidarCarritoRequest` (items: list[ValidarItemRequest] min_length=1, direccion_id: int) en `backend/pedidos/schemas.py`
- [x] 1.3 Agregar `StockInsuficienteItem` (producto_id, nombre, stockActual, cantidadSolicitada) en `backend/pedidos/schemas.py`
- [x] 1.4 Agregar `CambioPrecioItem` (producto_id, precioCarrito: Decimal, precioActual: Decimal) en `backend/pedidos/schemas.py`
- [x] 1.5 Agregar `ValidarCarritoResponse` (stockInsuficiente: list[StockInsuficienteItem], productosInvalidos: list[int], cambiosDePrecio: list[CambioPrecioItem], carritoVacio: bool, sinDireccion: bool) en `backend/pedidos/schemas.py`

## 2. Backend — Repository

- [x] 2.1 Abrir `backend/productos/repository.py` — agregar método `async def get_by_ids(self, producto_ids: list[int]) -> list[Producto]` usando `SELECT ... WHERE id IN (...)` (sin filtro disponible/eliminado_en — necesitamos detectar los inválidos)
- [x] 2.2 Verificar que `DireccionRepository` (en `backend/direcciones/repository.py`) tiene un método para contar o listar direcciones activas de un usuario — agregar `async def count_activas_by_usuario(self, usuario_id: int) -> int` si no existe

## 3. Backend — Service

- [x] 3.1 Abrir `backend/pedidos/service.py` (o crear `backend/pedidos/validation_service.py`) — agregar método `async def validar_carrito(request: ValidarCarritoRequest, usuario_id: int, uow) -> ValidarCarritoResponse`
- [x] 3.2 Implementar chequeo de carritoVacio: `if len(request.items) == 0` → raise HTTPException 422 RFC 7807
- [x] 3.3 Implementar chequeo de sinDireccion: `count = await uow.direcciones.count_activas_by_usuario(usuario_id)` → si 0 raise HTTPException 422 RFC 7807
- [x] 3.4 Implementar batch product lookup: `productos = await uow.productos.get_by_ids([i.producto_id for i in request.items])`
- [x] 3.5 Construir dict `productos_map: dict[int, Producto]` para lookups O(1)
- [x] 3.6 Iterar `request.items`: para cada ítem, si `producto_id` no en `productos_map` → agregar a `productosInvalidos`
- [x] 3.7 Iterar `request.items`: si producto en map pero `disponible=False` o `eliminado_en IS NOT NULL` → agregar a `productosInvalidos`
- [x] 3.8 Iterar `request.items`: si producto válido y `cantidad > producto.stock` → agregar a `stockInsuficiente`
- [x] 3.9 Iterar `request.items`: si producto válido y `abs(item.precio_carrito - producto.precio) > Decimal('0.01')` → agregar a `cambiosDePrecio`
- [x] 3.10 Retornar `ValidarCarritoResponse` con los cuatro campos poblados

## 4. Backend — Router

- [x] 4.1 Abrir `backend/pedidos/router.py` — agregar endpoint `@router.post("/validar", response_model=ValidarCarritoResponse, status_code=200)`
- [x] 4.2 Aplicar `current_user: Usuario = Depends(require_role([RolEnum.CLIENT]))` al endpoint
- [x] 4.3 Inyectar UoW via `Depends(get_uow)` (o el patrón que usa el proyecto)
- [x] 4.4 Llamar `return await validar_carrito(request, current_user.id, uow)` desde el router
- [x] 4.5 Verificar que el router de pedidos está registrado en `main.py` con prefix `/api/v1/pedidos`

## 5. Backend — Tests

- [x] 5.1 Crear `backend/tests/test_checkout_validation.py`
- [x] 5.2 Test: carrito vacío → HTTP 422
- [x] 5.3 Test: usuario sin direcciones → HTTP 422
- [x] 5.4 Test: carrito con stock suficiente y precios sin cambios → HTTP 200 con arrays vacíos
- [x] 5.5 Test: stock insuficiente en uno de los ítems → HTTP 200 con `stockInsuficiente` poblado
- [x] 5.6 Test: precio drift detectado (`abs > 0.01`) → HTTP 200 con `cambiosDePrecio` poblado
- [x] 5.7 Test: producto_id no existente en DB → HTTP 200 con `productosInvalidos` incluyendo ese ID
- [x] 5.8 Test: producto con `disponible=False` → HTTP 200 con `productosInvalidos` incluyendo ese ID
- [x] 5.9 Test: request sin JWT → HTTP 401
- [x] 5.10 Test: request con rol ADMIN → HTTP 403

## 6. Frontend — Types

- [x] 6.1 Crear `frontend/src/features/checkout/types/index.ts`
- [x] 6.2 Definir `ValidarItemRequest` (productoId: number, cantidad: number, precioCarrito: number)
- [x] 6.3 Definir `StockInsuficienteItem` (productoId: number, nombre: string, stockActual: number, cantidadSolicitada: number)
- [x] 6.4 Definir `CambioPrecioItem` (productoId: number, precioCarrito: number, precioActual: number)
- [x] 6.5 Definir `ValidarCarritoResponse` (stockInsuficiente, productosInvalidos: number[], cambiosDePrecio, carritoVacio: boolean, sinDireccion: boolean)

## 7. Frontend — CartStore (precio_carrito)

- [x] 7.1 Abrir `frontend/src/store/cartStore.ts` — agregar campo `precio_carrito: number` a la interfaz `CartItem`
- [x] 7.2 En `addItem()`: asignar `precio_carrito: producto.precio` (precio al momento de agregar)
- [x] 7.3 En `addItem()` para ítems duplicados: NO sobrescribir `precio_carrito` (mantener el valor original)
- [x] 7.4 Actualizar tests en `frontend/src/store/__tests__/cartStore.test.ts` — agregar scenario precio_carrito congelado

## 8. Frontend — useCheckoutValidation hook

- [x] 8.1 Crear `frontend/src/features/checkout/hooks/useCheckoutValidation.ts`
- [x] 8.2 Implementar `useMutation` de TanStack Query v5 que llama `POST /api/v1/pedidos/validar`
- [x] 8.3 Assemblar payload desde `useCartStore()`: mapear items → `{ productoId, cantidad, precioCarrito: item.precio_carrito ?? item.precio }`
- [x] 8.4 En `onError`: mostrar toast de error genérico ("Error de red al validar el carrito")
- [x] 8.5 Exportar `useCheckoutValidation` que devuelve `{ mutate, isPending, data, isError }`

## 9. Frontend — CheckoutValidationModal component

- [x] 9.1 Crear `frontend/src/features/checkout/components/CheckoutValidationModal.tsx`
- [x] 9.2 Props: `{ isOpen, onClose, onConfirm, validationResult: ValidarCarritoResponse | undefined, isHardBlock: boolean }`
- [x] 9.3 `isHardBlock = validationResult.carritoVacio || validationResult.sinDireccion`
- [x] 9.4 Sección de stock insuficiente: listar cada `stockInsuficienteItem` con nombre, stock actual, cantidad solicitada
- [x] 9.5 Sección de cambios de precio: listar cada `cambioPrecioItem` con nombre, precio anterior, precio nuevo
- [x] 9.6 Sección de productos inválidos: mostrar mensaje genérico "N productos ya no están disponibles" con instrucción de volver al carrito
- [x] 9.7 Si `isHardBlock`: mostrar solo botón "Volver al carrito" (sin botón "Continuar de todas formas")
- [x] 9.8 Si `!isHardBlock`: mostrar botones "Volver al carrito" y "Continuar de todas formas"
- [x] 9.9 Usar tokens semánticos Tailwind v4 (no clases hardcoded de colores) — rojo para errores, amarillo para warnings
- [x] 9.10 Agregar `role="dialog"`, `aria-modal="true"`, `aria-labelledby` para accesibilidad

## 10. Frontend — Checkout Page integration

- [x] 10.1 Crear `frontend/src/pages/CheckoutPage.tsx` (o abrir si ya existe)
- [x] 10.2 Llamar `useCheckoutValidation()` en el componente
- [x] 10.3 En `useEffect(() => { mutate() }, [])` — disparar validación al montar la página (solo una vez)
- [x] 10.4 Mientras `isPending`: mostrar spinner/skeleton en lugar del formulario de pedido
- [x] 10.5 Cuando `data` está disponible: calcular `isHardBlock` y `hasWarnings`
- [x] 10.6 Si `isHardBlock || hasWarnings`: abrir `CheckoutValidationModal` con los resultados
- [x] 10.7 Si validation clean: mostrar formulario de pedido directamente
- [x] 10.8 Agregar ruta `/checkout` al router en `frontend/src/app/` (si no existe)

## 11. Frontend — Tests

- [x] 11.1 Crear `frontend/src/features/checkout/__tests__/useCheckoutValidation.test.ts`
- [x] 11.2 Test: mutation llama al endpoint correcto con el payload correcto
- [x] 11.3 Test: `onError` dispara toast
- [x] 11.4 Crear `frontend/src/features/checkout/__tests__/CheckoutValidationModal.test.tsx`
- [x] 11.5 Test: renders stock shortage items correctamente
- [x] 11.6 Test: hard block muestra solo "Volver al carrito" (sin "Continuar")
- [x] 11.7 Test: soft warning muestra ambos botones

## 12. E2E — Playwright

- [x] 12.1 Crear `frontend/e2e/checkout-validation.spec.ts`
- [x] 12.2 E2E: usuario con carrito válido → llega a checkout sin modal
- [x] 12.3 E2E: usuario sin dirección → modal hard block en checkout
- [x] 12.4 E2E: mock API responde con stock insuficiente → modal soft warning → click "Continuar" → checkout form visible

## 13. Verificación post-change

- [x] 13.1 Leer `.agents/skills/post-change-verification/SKILL.md` y ejecutar health check completo
- [x] 13.2 Backend: `pytest backend/tests/test_checkout_validation.py -v` — todos pasan
- [x] 13.3 Backend: `black --check backend/` y `flake8 backend/` — sin errores
- [x] 13.4 Frontend: `npx vitest run` — todos los tests existentes + nuevos pasan
- [x] 13.5 Frontend: `npx tsc --noEmit` — sin errores de tipo
- [x] 13.6 Smoke test manual: levantar backend + frontend, agregar productos al carrito, navegar a /checkout, verificar que la validación se dispara
