# Food Store — Mapa Completo de Changes (SDD)

> **Documento de referencia**: Define todos los changes necesarios para desarrollar Food Store de principio a fin.
> **Última actualización**: 2026-05-12 (frontend-error-handling-global archivado)
> **Versión especificación**: 5.0 (ERD v5, Feature-First, SDD)
> **Versión mapa**: 3.1 — Estado real sincronizado + inconsistencias marcadas para reparar

---

## Leyenda de estados

| Símbolo | Significado |
|---------|-------------|
| ✅ | Archivado correctamente en OPSX |
| ❌ | Pendiente — no implementado |
| ⚠️ | Archivado con problema — requiere auditoría y reparación antes de continuar |
| 🔧 | Corrección aplicada al spec (no cambia código, cambia la descripción del change) |

---

## 🚨 INCONSISTENCIAS DETECTADAS — Reparar antes de continuar

Estas inconsistencias fueron identificadas al sincronizar el estado real del repo con el mapa v3.0 y las specs originales. El orquestador debe auditar y reparar cada una **antes** de implementar `route-protection-rbac`.

### INC-01 — `frontend-products-catalog-ui` archivado sin dependencias ⚠️ CRÍTICO

**Problema**: `frontend-products-catalog-ui` fue archivado el 2026-05-09 pero sus dependencias de backend NO están implementadas:
- `products-crud-core` ❌ pendiente
- `products-categories-association` ❌ pendiente
- `products-ingredients-association` ❌ pendiente
- `products-catalog-public` ❌ pendiente

El frontend del catálogo existe pero no tiene backend contra qué conectarse. Las queries de TanStack Query apuntan a endpoints que no existen. El componente compilará pero fallará en runtime con 404/500.

**Impacto**: Alto — cuando se implementen los changes de backend del catálogo, el frontend archivado puede tener contratos de API incorrectos (endpoints, schemas de respuesta, campos).

**Acción requerida**:
1. Auditar el código archivado en `openspec/changes/archive/2026-05-09-frontend-products-catalog-ui/`
2. Documentar qué endpoints asume el frontend (URLs, métodos, schemas de respuesta)
3. Al implementar `products-catalog-public`, verificar que los endpoints coincidan exactamente con lo que el frontend espera
4. Si hay discrepancia → crear change de corrección `fix-frontend-products-catalog-api-contract`
5. Marcar en Engram: `engram store foodstore:deuda-tecnica '{"inc": "INC-01", ...}'`

---

### ~~INC-02~~ — `es_predeterminada` vs `es_principal` ✅ RESUELTO 2026-05-11

**Solución aplicada**: Migración `004_rename_es_principal_to_es_predeterminada.py` creada. Actualizado `core/models.py` y `direcciones/schemas.py`. Commit `4cdddcc`.

---

### INC-03 — `backend-dev-infrastructure` marcado ⏳ en CHANGES.md pero archivado ✅ en OPSX 🔧

**Problema**: El archivo `docs/CHANGES.md` tiene `backend-dev-infrastructure` como ⏳ pendiente pero OPSX lo tiene archivado como `2026-04-24-backend-dev-infrastructure`. El mapa estaba stale.

**Impacto**: Bajo — solo es inconsistencia documental, el código existe.

**Acción requerida**: Corregido en este mapa v3.1 (marcado ✅). No requiere acción de código.

---

### ~~INC-04~~ — `INTEGER[]` para `ingredientes_excluidos` ✅ RESUELTO 2026-05-11

**Solución aplicada**: Campo era `VARCHAR` con JSON manual. Migración `005_ingredientes_excluidos_integer_array.py` convierte a `INTEGER[]` nativo con USING CASE. Actualizado `core/models.py` (List[int] + ARRAY(Integer)) y `pedidos/schemas.py`. Commit `4cdddcc`.

---

### INC-05 — `backend-fastapi-core-setup` archivado con nombre diferente 🔧

**Problema**: El change está en OPSX como `2026-04-24-backend-setup` pero en el mapa figura como `backend-fastapi-core-setup`.

**Impacto**: Bajo — solo naming. No afecta código.

**Acción requerida**: Documentado aquí. Al hacer `openspec list`, usar el nombre real del archivo. No requiere acción de código.

---

### INC-06 — `backend-postgres-alembic-seed` archivado dos veces 🔧

**Problema**: Aparece archivado en `2026-05-06` y `2026-05-08`. Posible re-run o corrección aplicada fuera de un change formal.

**Impacto**: Bajo-medio — verificar si la segunda corrección introdujo cambios no documentados (por ejemplo, si ahí se agregó el campo `activo` en Usuario).

**Acción requerida**:
1. Comparar diff entre ambos archives
2. Documentar en Engram qué cambió entre el primer y segundo run
3. Verificar que el campo `activo BOOLEAN DEFAULT TRUE` existe en la migración actual

---

## EPIC 00 — Infraestructura y Setup

### ✅ `infrastructure-repo-setup`
Archivado: `2026-04-24-infrastructure-repo-setup`

Monorepo Git inicializado. Estructura `/backend` (feature-first) + `/frontend` (FSD). `.gitignore`, `.env.example`, `README.md`.

**Dependencias**: Ninguna

---

### ✅ `backend-fastapi-core-setup`
Archivado: `2026-04-24-backend-setup` *(nombre en OPSX difiere — ver INC-05)*

FastAPI + uvicorn configurado. Dependencias core instaladas. `main.py` con CORS + rate limiting. `core/config.py`, `core/database.py`, `core/security.py`. Swagger en `/docs`.

**Dependencias**: `infrastructure-repo-setup`

---

### ✅ `backend-dev-infrastructure`
Archivado: `2026-04-24-backend-dev-infrastructure` *(CHANGES.md anterior lo marcaba ⏳ — corregido en INC-03)*

Docker Compose con PostgreSQL 16 Alpine. `psycopg[binary]==3.1.17`. Seed idempotente. README actualizado.

**Dependencias**: `backend-fastapi-core-setup`

---

### ✅ `backend-postgres-alembic-seed`
Archivado: `2026-05-06` y `2026-05-08` *(doble run — ver INC-06)*

16 tablas ERD v5 creadas con Alembic. Campo `activo BOOLEAN DEFAULT TRUE` en Usuario *(verificar — INC-06)*. Seed: 4 Roles, 6 EstadoPedido, 3 FormaPago, 1 admin. Soft delete con `eliminado_en`. Campos auditoría.

**🔧 Verificar**: campo `personalizacion` como `INTEGER[]` en `DetallePedido` (INC-04). Campo `es_predeterminada` en `DireccionEntrega` (INC-02).

**Dependencias**: `backend-fastapi-core-setup`

---

### ✅ `backend-patterns-base-repository-uow`
Archivado: `2026-05-06`

`BaseRepository[T]` genérico con `get_by_id`, `list_all`, `count`, `create`, `update`, `soft_delete`, `hard_delete`. `UnitOfWork` como context manager async. `get_current_user()`. `require_role()`. Middleware RFC 7807.

**Dependencias**: `backend-postgres-alembic-seed`

---

### ✅ `frontend-react-vite-setup`
Archivado: `2026-05-06`

React 18 + TypeScript + Vite. Dependencias instaladas. TypeScript strict mode. Tailwind + PostCSS. Axios con base URL. Routing base. QueryClient configurado.

**Dependencias**: `infrastructure-repo-setup`

---

### ✅ `frontend-zustand-stores-setup`
Archivado: `2026-05-08`

4 stores Zustand: `authStore` (tokens, persistencia), `cartStore` (items, persistencia completa), `paymentStore` (sin persistencia), `uiStore` (theme persistido). Suscripción por slice.

**Dependencias**: `frontend-react-vite-setup`

---

### ✅ `backend-axios-jwt-interceptor`
Archivado: `2026-05-08`

Instancia Axios centralizada en `shared/api/axios.ts`. Interceptor de request (adjunta Bearer token). Interceptor de response (detecta 401, refresca, reintenta, cola de requests). Fallback a login si refresh falla.

**Dependencias**: `frontend-zustand-stores-setup`

---

### ✅ `backend-error-handling-rfc7807`
Archivado: `2026-05-08`

Middleware global RFC 7807 (`type`, `title`, `status`, `detail`, `instance`). Errores de validación con detalle por campo. Sin stack traces en producción.

**Dependencias**: `backend-fastapi-core-setup`

---

### ✅ `backend-input-validation-sanitization`
Archivado: `2026-05-08`

Schemas Pydantic v2. Validaciones: emails, longitudes, rangos. Queries parametrizadas. Sanitización XSS.

**Dependencias**: `backend-fastapi-core-setup`

---

## EPIC 01 — Autenticación y Autorización

### ✅ `auth-registration`
Archivado: EPIC 01

`POST /api/v1/auth/register`. Email único, bcrypt cost ≥ 12, rol CLIENT automático. Access token 30min + refresh token 7días. Rate limiting: 3 registros/IP/hora (RN-AU06, US-073).

**Dependencias**: `backend-patterns-base-repository-uow`

---

### ✅ `auth-login`
Archivado: EPIC 01

`POST /api/v1/auth/login`. Rate limiting: 5 intentos fallidos/IP/15min. Verifica `activo=true` (403 si desactivado, US-055). No diferencia email/password incorrecto (RN-AU08). JWT access + refresh UUID en BD. Headers `X-RateLimit-*`.

**Dependencias**: `auth-registration`

---

### ✅ `auth-token-refresh`
Archivado: EPIC 01

`POST /api/v1/auth/refresh`. Rotación de refresh token (RN-AU04). Detección replay attack → revoca todos los tokens del usuario (RN-AU05).

**Dependencias**: `auth-login`

---

### ✅ `auth-logout`
Archivado: EPIC 01

`POST /api/v1/auth/logout`. Revoca refresh token (`revoked_at = now()`). Frontend limpia authStore. Retorna 204.

**Dependencias**: `auth-login`

---

### ✅ `rbac-roles-management`
Archivado: EPIC 01

4 roles fijos con IDs estables: ADMIN(1), STOCK(2), PEDIDOS(3), CLIENT(4). Tabla UsuarioRol N:M con UNIQUE compuesta. `PUT /api/admin/users/:id/role` (solo ADMIN). Validación: no quitarse ADMIN si último admin (RN-RB04). Al cambiar rol → invalidar todos los refresh tokens del usuario (US-054).

**Dependencias**: `auth-registration`

---

### ✅ `route-protection-rbac`
Archivado: `2026-05-11-route-protection-rbac`

`require_role(roles: list[str])` factory en `core/dependencies.py`. Retorna dependency FastAPI que verifica rol del usuario autenticado. 401 sin token, 403 con rol insuficiente (RFC 7807). Activo check en login (403 "Cuenta desactivada"). Guards aplicados al endpoint existente `PUT /admin/users/:id/role`. Routers futuros (productos, pedidos, admin, etc.) tienen mapping documentado en `test_route_protection.py` sección 7 para aplicar al implementarlos. 13 tests pasando.

**Dependencias**: `rbac-roles-management`

---

### ✅ `frontend-navigation-by-role`
Archivado: `2026-05-12-frontend-navigation-by-role`

Componente Navigation/Sidebar con menú dinámico por rol. CLIENT: Catálogo, Carrito, Mis Pedidos, Mi Perfil, Mis Direcciones. STOCK: Productos, Categorías, Ingredientes. PEDIDOS: Panel Pedidos. ADMIN: todo + Usuarios + Métricas + Configuración. No autenticado: Catálogo, Login, Registrarse. `useNavLinks()` hook con `_hasHydrated` guard. 123/123 tests pasando.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `rbac-roles-management`

---

### ✅ `frontend-route-guards-auth`
Archivado: `2026-05-12-frontend-route-guards-auth`

`ProtectedRoute` como layout route (react-router-dom v6). Guard 3 niveles: `_hasHydrated` → spinner, `!isAuthenticated` → `/login`, rol insuficiente → `/403`. `ForbiddenPage` con WCAG AA. Router.tsx reescrito con grupos de rutas por rol. 25/25 tasks, 128/128 tests.

**Skills**: `tailwind-design-system`, `ui-design-system`
**Dependencias**: `frontend-navigation-by-role`

---

### ✅ `frontend-error-handling-global`
Archivado: `2026-05-12-frontend-error-handling-global`

ErrorBoundary refactored a Tailwind v4 + botón "Ir al inicio". ToastContainer con auto-dismiss (4/5/6s), cierre manual, íconos lucide-react, límite 5 toasts. Interceptor Axios mapea 400/403/404/422/429/500 + red a mensajes en español vía uiStore. 159/159 tests.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `frontend-state-management`
**Dependencias**: `backend-error-handling-rfc7807`

---

## EPIC 02 — Layout Base

### ❌ `frontend-layout-components-shared`

Layout con Navbar, Sidebar, main, Footer. Componentes atómicos: Button, Input, Card, Modal, Toast, Skeleton, Badge. Sistema de iconos. Variables Tailwind. Responsive mobile-first.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `frontend-route-guards-auth`

---

## EPIC 03 — Categorías

### ❌ `categories-crud-hierarchical`

Modelo `Categoria` con `padre_id` autoreferencial. `POST/GET/PUT/DELETE /api/v1/categorias`. Árbol anidado con CTE recursivo. No crear ciclos. No eliminar con productos activos. Soft delete.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `route-protection-rbac`

---

## EPIC 04 — Ingredientes

### ❌ `ingredients-crud-allergens`

Modelo `Ingrediente` con `es_alergeno`. `POST/GET/PUT/DELETE /api/v1/ingredientes`. UNIQUE en nombre. Soft delete.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `route-protection-rbac`

---

## EPIC 05 — Productos y Catálogo

### ❌ `products-crud-core`

Modelo `Producto`. `POST/GET/PUT/PATCH/DELETE /api/v1/productos`. Precio NUMERIC(10,2). Stock INTEGER ≥ 0. Soft delete. `?incluir_eliminados=true` para admin (RN-CA10).

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `route-protection-rbac`

---

### ❌ `products-categories-association`

Tabla pivote `ProductoCategoria`. `PUT/DELETE /api/v1/productos/:id/categorias`.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `products-crud-core`, `categories-crud-hierarchical`

---

### ❌ `products-ingredients-association`

Tabla pivote `ProductoIngrediente` con `es_removible`. `PUT/DELETE /api/v1/productos/:id/ingredientes`. Filtro `?excluirAlergenos=1,3,7`.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `products-crud-core`, `ingredients-crud-allergens`

---

### ❌ `products-catalog-public`

`GET /api/v1/productos` público con paginación, búsqueda ILIKE, filtro por categoría, exclusión de alergenos. `GET /api/v1/productos/:id` con categorías e ingredientes.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `products-categories-association`, `products-ingredients-association`

---

### ⚠️ `frontend-products-catalog-ui`
Archivado: `2026-05-09` — **ARCHIVADO SIN DEPENDENCIAS DE BACKEND (INC-01)**

Página Catalog con grid, ProductCard, filtros, paginación, skeletons, "Agregar al carrito".

**⚠️ ACCIÓN REQUERIDA al implementar `products-catalog-public`**:
- Auditar `openspec/changes/archive/2026-05-09-frontend-products-catalog-ui/`
- Verificar contratos de API: URLs, métodos, schemas de respuesta esperados
- Si hay discrepancia con los endpoints reales → crear `fix-frontend-products-catalog-api-contract`

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias originales no cumplidas**: `products-catalog-public` ❌

---

## EPIC 06 — Perfil de Cliente

### ❌ `backend-user-profile-endpoints`

`GET/PUT /api/v1/perfil`. `POST /api/v1/perfil/cambiar-password` — valida password actual, hashea nueva, **revoca todos los refresh tokens activos** (US-063, RN-AU04).

**Skills**: `fastapi-python`
**Dependencias**: `route-protection-rbac`

---

### ❌ `frontend-user-profile-ui`

Página MyProfile. Form editar nombre/teléfono. Cambio de contraseña. Última sesión.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `backend-user-profile-endpoints`, `frontend-layout-components-shared`

---

## EPIC 07 — Direcciones de Entrega

### ❌ `addresses-crud-by-user`

Modelo `DireccionEntrega` con campo `es_predeterminada` *(🔧 verificar INC-02 — puede estar como `es_principal` en BD)*. `POST/GET/PUT/PATCH/DELETE /api/v1/direcciones`. Primera dirección → predeterminada automática (RN-DI01). Solo una predeterminada por usuario (RN-DI02). Ownership por userId JWT (RN-DI03).

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `route-protection-rbac`

---

### ❌ `frontend-addresses-ui`

Página MyAddresses. AddressCard con editar/eliminar/predeterminada. Form AddressForm.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `addresses-crud-by-user`, `frontend-layout-components-shared`

---

## EPIC 08 — Carrito de Compras

### ❌ `frontend-shopping-cart-zustand`

Completar `cartStore`: `addItem`, `removeItem`, `updateQuantity`, `clearCart`, selectores, persistencia localStorage. Personalización como array de IDs de ingredientes a excluir (RN-CR04, RN-CR05). Incrementar cantidad si producto ya en carrito (RN-CR03).

**Skills**: `frontend-design`
**Dependencias**: `frontend-zustand-stores-setup`

---

### ❌ `frontend-shopping-cart-ui`

CartDrawer con items, +/-, eliminar, vaciar, total, botón checkout. CartIcon en Navbar con contador. Estado vacío.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `frontend-shopping-cart-zustand`, `frontend-layout-components-shared`

---

## EPIC 09 — Validaciones Pre-Checkout *(NUEVO en v3.0)*

### ❌ `checkout-pre-validation`

`POST /api/v1/pedidos/validar` (CLIENT). Verifica disponibilidad y stock. Compara precios actuales vs carrito. Response: `stockInsuficiente`, `productosInvalidos`, `cambiosDePrecio`. Frontend: llamar al entrar al Checkout, mostrar alertas/modal de confirmación.

**Skills**: `fastapi-python`, `postgres`, `frontend-design`
**Dependencias**: `products-crud-core`, `frontend-shopping-cart-zustand`

---

## EPIC 10 — Pedidos

### ❌ `orders-fsm-backend`

FSM 6 estados: PENDIENTE→CONFIRMADO→EN_PREPARACIÓN→EN_CAMINO→ENTREGADO + CANCELADO. `HistorialEstadoPedido` append-only. Snapshot precio + dirección. UoW atómico. Personalización como `INTEGER[]` (RN-PE07). `SELECT FOR UPDATE` para stock (RN-PE04). Rate limiting creación: 10/usuario/hora (US-073). PENDIENTE→CONFIRMADO solo por Sistema/webhook (RN-FS02).

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `backend-patterns-base-repository-uow`, `addresses-crud-by-user`, `products-crud-core`

---

### ❌ `orders-api-endpoints`

`POST /api/v1/pedidos`, `GET /api/v1/pedidos`, `GET /api/v1/pedidos/:id`, `PATCH /api/v1/pedidos/:id/avanzar`, `GET /api/v1/pedidos/:id/historial`, `DELETE /api/v1/pedidos/:id` (cancelar). Permisos por rol.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `orders-fsm-backend`

---

### ❌ `frontend-orders-listing-ui`

Página MyOrders (CLIENT). Página OrdersPanel (ADMIN/PEDIDOS). OrderCard con estado badge. Paginación, filtros, skeletons.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `orders-api-endpoints`, `frontend-layout-components-shared`

---

### ❌ `frontend-orders-detail-ui`

Página OrderDetail. Items con snapshots. Timeline de estados (HistorialEstadoPedido). Botones de acción por estado y rol. Cancelar con confirmación.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `orders-api-endpoints`, `frontend-layout-components-shared`

---

### ❌ `frontend-orders-management-admin`

Tabla admin con filtros, bulk actions. Componente `OrderConfirmation` post-creación (US-071). Páginas `PaymentSuccess`, `PaymentFailure`, `PaymentPending` para callbacks MP (US-072).

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `frontend-orders-listing-ui`, `frontend-orders-detail-ui`

---

## EPIC 11 — Pagos

### ❌ `payments-mercadopago-integration-backend`

Modelo `Pago` con `idempotency_key`. `POST /api/v1/pagos/crear`. Webhook `POST /api/v1/pagos/webhook` — validar firma, consultar API MP, idempotencia (RN-PA02), approved→PENDIENTE→CONFIRMADO+stock (RN-PA05). `GET /api/v1/pagos/:pedido_id`.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `orders-fsm-backend`

---

### ❌ `frontend-payment-checkout-ui`

Checkout en pasos. Llama a `POST /api/v1/pedidos/validar` al entrar. CardPayment SDK MP (tokenización cliente). Estados: procesando/aprobado/rechazado/pendiente. Integración paymentStore.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `payments-mercadopago-integration-backend`, `addresses-crud-by-user`, `frontend-shopping-cart-zustand`, `checkout-pre-validation`

---

### ❌ `frontend-payment-status-polling`

Polling cada 30s a `GET /api/v1/pagos/:pedido_id` mientras estado PENDIENTE. Detener cuando no sea PENDIENTE.

**Skills**: `frontend-design`
**Dependencias**: `frontend-payment-checkout-ui`

---

## EPIC 12 — Panel de Administración

### ❌ `backend-admin-users-endpoints` *(NUEVO en v3.0 — gap INC anterior)*

`GET /api/v1/admin/usuarios` — paginación, búsqueda, filtro por rol. `PUT /api/v1/admin/usuarios/:id` — editar nombre/roles, invalida refresh tokens al cambiar rol. `PATCH /api/v1/admin/usuarios/:id/estado` — campo `activo`, al desactivar revoca tokens.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `rbac-roles-management`

---

### ❌ `admin-dashboard-metrics`

`GET /api/v1/admin/metricas/resumen` con filtro fecha. `GET /api/v1/admin/metricas/ventas?granularidad=dia|semana|mes` (DATE_TRUNC). `GET /api/v1/admin/metricas/productos-top`. `GET /api/v1/admin/metricas/pedidos-por-estado`.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `orders-fsm-backend`, `products-crud-core`

---

### ❌ `frontend-admin-dashboard-ui`

KPI cards. Selector rango fechas. LineChart ventas, BarChart top productos, PieChart estados, tabla stock bajo. Refresh cada 5min.

**Skills**: `frontend-design`, `tailwind-design-system`, `postgres`
**Dependencias**: `admin-dashboard-metrics`, `frontend-layout-components-shared`

---

### ❌ `admin-categories-management-ui`
**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `categories-crud-hierarchical`, `frontend-layout-components-shared`

---

### ❌ `admin-products-management-ui`
**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `products-crud-core`, `products-categories-association`, `products-ingredients-association`, `frontend-layout-components-shared`

---

### ❌ `admin-stock-management-ui`
**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `admin-products-management-ui`

---

### ❌ `admin-users-management-ui`

Tabla usuarios con badge `activo`. Acciones: editar, activar/desactivar, cambiar roles. Filtro por rol/estado.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `backend-admin-users-endpoints`, `frontend-layout-components-shared`

---

### ❌ `admin-ingredients-management-ui`
**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `ingredients-crud-allergens`, `frontend-layout-components-shared`

---

## EPIC 13 — Patrones Frontend *(NUEVO en v3.1)*

### ❌ `frontend-widgets-layer`

Capa `widgets/` FSD. Componentes compuestos: `CartSidebar` (drawer completo), `OrderTimeline` (historial estados), `ProductGrid` (grid + filtros + paginación), `DashboardLayout`. Estos widgets componen features y entities en bloques reutilizables.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `frontend-layout-components-shared`, `frontend-shopping-cart-ui`

---

### ❌ `frontend-patterns-hooks-optimistic`

Custom hooks evaluados en rúbrica: `useProductos(filtros)` (TanStack Query + paginación + debounce), `usePedidos(filtros)`, `useCarrito()` (wrapper cartStore + validaciones), `useAuth()`. Optimistic updates en mutaciones del carrito con `onMutate/onError/onSettled`.

**Skills**: `frontend-design`
**Dependencias**: `frontend-shopping-cart-zustand`, `frontend-orders-listing-ui`

---

## EPIC 14 — Configuración del Sistema *(NUEVO en v3.0)*

### ❌ `system-configuration-backend`

Modelo `Configuracion` (clave UNIQUE, valor, descripcion, actualizado_por FK Usuario, actualizado_en). Seed inicial. `GET/PUT /api/v1/admin/configuracion`. Cambios sin reiniciar. Auditoría de quién modificó.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `route-protection-rbac`

---

### ❌ `frontend-system-configuration-ui`

Página AdminConfig. Tabla/form clave-valor editable inline. Toast al guardar. Muestra último modificador y fecha.

**Skills**: `frontend-design`, `tailwind-design-system`
**Dependencias**: `system-configuration-backend`, `frontend-layout-components-shared`

---

## EPIC 15 — Entrega Final

### ❌ `backend-comprehensive-testing`

pytest cobertura > 60%. Tests: auth (login, registro, refresh, replay attack, bloqueo inactivo), pedidos (FSM, cancelación, stock), pagos (webhook, idempotencia), categorías (CRUD, ciclos), productos, usuarios (activar/desactivar, cambio rol). Mocking MP SDK.

**Dependencias**: todos los changes backend

---

### ❌ `documentation-openapi-complete`

Swagger `/docs` con todos los endpoints. Ejemplos request/response. Errores documentados. Auth bearer. Rate limiting documentado.

**Dependencias**: todos los routers

---

### ❌ `deploy-production` *(NUEVO en v3.1 — +10 pts rúbrica)*

Deploy backend en Railway/Render/Fly.io. Frontend en Vercel/Netlify. Variables de entorno de producción en `.env.example`. URL accesible en README. MercadoPago Sandbox configurado en producción.

**Skills**: `documentation-writer`
**Dependencias**: todos los changes anteriores

---

### ❌ `repository-setup-final-checklist`

README completo. `.env.example` con todas las variables. `.gitignore` correcto. Repo público GitHub. Screenshots ≥ 10 pantallas. Video demostración 5-10 min. Verificar funcionamiento en máquina limpia.

**Dependencias**: todos los changes anteriores

---

## Orden de Implementación

```
BLOQUE 0 — REPARACIÓN (hacer ANTES de continuar)
├─ Auditar INC-01: frontend-products-catalog-ui archivado sin backend
├─ Verificar INC-02: es_predeterminada vs es_principal en BD
├─ Verificar INC-04: INTEGER[] en personalizacion en BD
└─ Verificar INC-06: diff entre doble run de backend-postgres-alembic-seed

BLOQUE 1 — Infraestructura ✅ COMPLETO
(todos archivados — ver sección EPIC 00)

BLOQUE 2 — Auth (parcialmente completo)
├─ ✅ auth-registration
├─ ✅ auth-login
├─ ✅ auth-token-refresh
├─ ✅ auth-logout
├─ ✅ rbac-roles-management
├─ ✅ route-protection-rbac
├─ ✅ frontend-navigation-by-role
├─ ❌ frontend-route-guards-auth     ← PRÓXIMO
└─ ❌ frontend-error-handling-global

BLOQUE 3 — Layout + Catálogo
├─ ❌ frontend-layout-components-shared
├─ ❌ categories-crud-hierarchical
├─ ❌ ingredients-crud-allergens
├─ ❌ products-crud-core
├─ ❌ products-categories-association
├─ ❌ products-ingredients-association
├─ ❌ products-catalog-public
└─ ⚠️  frontend-products-catalog-ui  ← AUDITAR al llegar aquí (INC-01)

BLOQUE 4 — Perfil + Direcciones + Carrito
├─ ❌ backend-user-profile-endpoints
├─ ❌ frontend-user-profile-ui
├─ ❌ addresses-crud-by-user         ← verificar INC-02
├─ ❌ frontend-addresses-ui
├─ ❌ frontend-shopping-cart-zustand
└─ ❌ frontend-shopping-cart-ui

BLOQUE 5 — Pre-checkout + Pedidos
├─ ❌ checkout-pre-validation
├─ ❌ orders-fsm-backend             ← verificar INC-04 (INTEGER[])
├─ ❌ orders-api-endpoints
├─ ❌ frontend-orders-listing-ui
├─ ❌ frontend-orders-detail-ui
└─ ❌ frontend-orders-management-admin

BLOQUE 6 — Pagos
├─ ❌ payments-mercadopago-integration-backend
├─ ❌ frontend-payment-checkout-ui
└─ ❌ frontend-payment-status-polling

BLOQUE 7 — Admin
├─ ❌ backend-admin-users-endpoints
├─ ❌ admin-dashboard-metrics
├─ ❌ frontend-admin-dashboard-ui
├─ ❌ admin-categories-management-ui
├─ ❌ admin-products-management-ui
├─ ❌ admin-stock-management-ui
├─ ❌ admin-users-management-ui
└─ ❌ admin-ingredients-management-ui

BLOQUE 8 — Patrones + Configuración
├─ ❌ frontend-widgets-layer
├─ ❌ frontend-patterns-hooks-optimistic
├─ ❌ system-configuration-backend
└─ ❌ frontend-system-configuration-ui

BLOQUE 9 — Entrega Final
├─ ❌ backend-comprehensive-testing
├─ ❌ documentation-openapi-complete
├─ ❌ deploy-production
└─ ❌ repository-setup-final-checklist
```

---

## Historial de versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 3.1 | 2026-05-11 | Estado real sincronizado con OPSX archive. 6 inconsistencias documentadas (INC-01 a INC-06). BLOQUE 0 de reparación agregado. Nuevos changes: `frontend-widgets-layer`, `frontend-patterns-hooks-optimistic`, `deploy-production`. Corrección naming `es_predeterminada`. `INTEGER[]` explicitado en pedidos. `frontend-products-catalog-ui` marcado ⚠️. |
| 3.0 | 2026-05-11 | Análisis de gaps completo. Changes nuevos: checkout-pre-validation, backend-admin-users-endpoints, system-configuration-backend, frontend-system-configuration-ui. |
| 2.0 | 2026-04-24 | backend-dev-infrastructure agregado |
| 1.0 | 2026-04-21 | Documento inicial |
