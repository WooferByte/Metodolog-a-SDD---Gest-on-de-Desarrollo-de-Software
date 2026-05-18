# Food Store — Mapa Completo de Changes (SDD)

> **Documento de referencia**: Define todos los changes necesarios para desarrollar Food Store de principio a fin.
> **Última actualización**: 2026-05-18 (frontend-payment-checkout-fixes archivado)
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

### ~~INC-01~~ — `frontend-products-catalog-ui` archivado sin dependencias ✅ RESUELTO 2026-05-13

**Resolución**: Backend completo (products-crud-core, products-categories-association, products-ingredients-association, products-catalog-public — todos archivados 2026-05-13). Contrato de API auditado y corregido en `useProductsCatalog.ts` (2026-05-13): `busqueda→q`, `categoria→categoria_id`, `limit→size`, response envelope `{items,total,page,size,pages}`. No fue necesario crear `fix-frontend-products-catalog-api-contract`.

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

### ✅ `frontend-layout-components-shared`
Archivado: `2026-05-12-frontend-layout-components-shared`

AppLayout + Sidebar (mobile overlay / desktop persistente) + Footer. Tokens @theme OKLCH + dark mode vía uiStore. Primitivas UI: Button (5 variantes), Input, Card (compound), Modal (native dialog), Badge, Skeleton. cn() utility (clsx + tailwind-merge). Navbar extendido con hamburger + theme toggle. 209/209 tests.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `zustand-state-management`
**Dependencias**: `frontend-route-guards-auth`

### ✅ `frontend-refactor-apply-skills`
Archivado: `2026-05-13-frontend-refactor-apply-skills`

Aplicación retroactiva de skills a 4 changes ejecutados sin ellas. Router.tsx: `React.lazy` + `Suspense` (8 page chunks). authStore + cartStore: `devtools(persist())` middleware. `withAuth` HOC deprecated eliminado, `ProtectedRoute.tsx` separado. `Spinner.tsx` extraído. Tokens semánticos en todos los componentes de `products/components/`. ARIA: `role="list"`, `aria-modal`, `aria-live`, `aria-label`. `placeholderData: keepPreviousData` en `useProductsCatalog`. Setup Playwright: `playwright.config.ts` + `e2e/helpers/auth.ts` + `e2e/route-guards.spec.ts` (4 tests de guards). `vitest.config.ts`: exclude `e2e/**`. 209/209 tests.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `frontend-state-management`, `zustand-state-management`, `testing-e2e-playwright`
**Evidencia**: `openspec/changes/archive/2026-05-13-frontend-refactor-apply-skills/`

### ✅ `frontend-nav-responsive-fix`
Archivado: `2026-05-13-frontend-nav-responsive-fix`

Corrección de doble navegación señalada por el profesor: el Navbar duplicaba los links del Sidebar en todos los breakpoints. Fix: eliminados `useNavLinks` import, hook call, y bloque `navLinks.map()` del Navbar. El Navbar queda exclusivamente con hamburger + brand + user info + theme toggle. `bg-red-600` migrado a token `bg-destructive`. El Sidebar es el único punto de navegación en todos los breakpoints. 209/209 tests.

**Skills**: `tailwind-design-system`, `ui-design-system`
**Evidencia**: `openspec/changes/archive/2026-05-13-frontend-nav-responsive-fix/`

---

## EPIC 03 — Categorías

### ✅ `categories-crud-hierarchical`
Archivado: `2026-05-12-categories-crud-hierarchical`

7 endpoints REST. CTE recursivo PostgreSQL para árbol con `depth`. Anti-ciclo iterativo en PUT. Guard productos activos en DELETE. Migración 006: índice parcial `idx_categorias_padre_id WHERE eliminado_en IS NULL`. 20/20 tests.

**Skills**: `python-fastapi-ddd-skill`, `supabase-postgres-best-practices`, `api-design`, `post-change-verification`
**Dependencias**: `route-protection-rbac`

---

## EPIC 04 — Ingredientes

### ✅ `ingredients-crud-allergens`
Archivado: `2026-05-13-ingredients-crud-allergens`

CRUD ingredientes con `es_alergeno`. Filtro `?es_alergeno=true/false`. Guard productos activos en DELETE. Nombre UNIQUE con 409. Soft delete. Migración 007: índice parcial. 18/18 tests.

**Skills**: `python-fastapi-ddd-skill`, `supabase-postgres-best-practices`, `api-design`, `post-change-verification`
**Dependencias**: `route-protection-rbac`

---

## EPIC 05 — Productos y Catálogo

### ✅ `products-crud-core` (archivado 2026-05-13)

Modelo `Producto`. `POST/GET/PUT/PATCH/DELETE /api/v1/productos`. Precio NUMERIC(10,2). Stock INTEGER ≥ 0. Soft delete. `?incluir_eliminados=true` para admin (RN-CA10).

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `route-protection-rbac`
**Evidencia**: `openspec/changes/archive/2026-05-13-products-crud-core/`

---

### ✅ `products-categories-association` (archivado 2026-05-13)

Tabla pivote `ProductoCategoria`. `PUT/DELETE /api/v1/productos/:id/categorias`.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `products-crud-core`, `categories-crud-hierarchical`
**Evidencia**: `openspec/changes/archive/2026-05-13-products-categories-association/`

---

### ✅ `products-ingredients-association` (archivado 2026-05-13)

Tabla pivote `ProductoIngrediente` con `es_removible`. `PUT/DELETE /api/v1/productos/:id/ingredientes`. Filtro `?excluirAlergenos=1,3,7`.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `products-crud-core`, `ingredients-crud-allergens`
**Evidencia**: `openspec/changes/archive/2026-05-13-products-ingredients-association/`

---

### ✅ `products-catalog-public` (archivado 2026-05-13)

`GET /api/v1/productos` público con paginación, búsqueda ILIKE, filtro por categoría, exclusión de alergenos. `GET /api/v1/productos/:id` con categorías e ingredientes.

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `products-categories-association`, `products-ingredients-association`
**Evidencia**: `openspec/changes/archive/2026-05-13-products-catalog-public/`

---

### ✅ `frontend-products-catalog-ui`
Archivado: `2026-05-09` — contrato API corregido 2026-05-13 (INC-01 ✅ resuelto)

Página Catalog con grid, ProductCard, filtros, paginación, skeletons, "Agregar al carrito". Contrato corregido: `q=`, `categoria_id=`, `size/pages` envelope.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `frontend-state-management`
**Dependencias**: `products-catalog-public` ✅

---

## EPIC 06 — Perfil de Cliente

### ✅ `backend-user-profile-endpoints`
Archivado: `2026-05-13-backend-user-profile-endpoints`

`GET/PUT /api/v1/perfil`. `POST /api/v1/perfil/cambiar-password` — valida password actual, hashea nueva (bcrypt cost=12), revoca TODOS los refresh tokens activos (US-063, RN-AU04). 3 archivos nuevos: `perfil_schemas.py`, `perfil_service.py`, `perfil_router.py`. 22/22 tests.

**Skills**: `python-fastapi-ddd-skill`, `api-design`, `jwt-security`, `post-change-verification`
**Dependencias**: `route-protection-rbac` ✅

---

### ✅ `frontend-user-profile-ui`
Archivado: `2026-05-13-frontend-user-profile-ui`

Página Profile. ProfileInfo (read-only, dl/dt/dd, Skeleton, Badge roles). EditProfileForm (dirty check, validación client-side, aria-live). ChangePasswordForm (show/hide toggle aria-pressed, countdown logout). 3 hooks TanStack Query (GET/PUT/POST 204). 5 E2E Playwright. Solo tokens semánticos, ARIA completo, responsive. 225/225 vitest.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `frontend-state-management`, `zustand-state-management`, `testing-e2e-playwright`
**Dependencias**: `backend-user-profile-endpoints` ✅, `frontend-layout-components-shared` ✅

---

### ✅ `frontend-catalog-profile-fixes`
Archivado: `2026-05-14-frontend-catalog-profile-fixes`
**Evidencia**: `openspec/changes/archive/2026-05-14-frontend-catalog-profile-fixes/`

Fixes post-entrega EPIC 05 y 06. (1) Toast normalisation: `safeString()` en interceptor Axios garantiza que `toast.message` siempre sea string primitivo; `String()` defensivo en `ToastContainer`. (2) Catalog filter UI: filtros móviles como overlay fijo (`hidden md:block`), grid full-width cuando colapsado, backdrop, tokens semánticos `@theme`, `accent-primary` en checkboxes, `hover:bg-muted/50`, `focus:ring-2 focus:ring-ring` WCAG AA. (3) ChangePasswordForm: validación cliente solo formato (required + mín 8 chars), eliminada comparación client-side passwordActual vs nuevaPassword, backend es autoridad. 3 nuevas specs capturadas: `toast-error-normalisation`, `change-password-form`, `catalog-filter-ui`.

**Skills**: `tailwind-design-system`, `ui-design-system`, `frontend-state-management`, `vercel-react-best-practices`, `testing-e2e-playwright`, `jwt-security`
**Dependencias**: `frontend-user-profile-ui` ✅, `frontend-products-catalog-ui` ✅, `frontend-error-handling-global` ✅

---

## EPIC 07 — Direcciones de Entrega

### ✅ `addresses-crud-by-user`
Archivado: `2026-05-14-addresses-crud-by-user`
**Evidencia**: `openspec/changes/archive/2026-05-14-addresses-crud-by-user/`

Modelo `DireccionEntrega` con campo `es_predeterminada` *(INC-02 ✅ resuelto)*. `POST/GET/PUT/PATCH/DELETE /api/v1/direcciones`. Primera dirección → predeterminada automática (RN-DI01). Solo una predeterminada por usuario (RN-DI02). Ownership por userId JWT (RN-DI03).

**Skills**: `fastapi-python`, `postgres`
**Dependencias**: `route-protection-rbac`

---

### ✅ `frontend-addresses-ui`
Archivado: `2026-05-14-frontend-addresses-ui`
**Evidencia**: `openspec/changes/archive/2026-05-14-frontend-addresses-ui/`

Página `MyAddressesPage` en `/direcciones` para CLIENT. `AddressCard` con editar/eliminar/marcar predeterminada. `AddressForm` modal reutilizable crear/editar. `DeleteAddressDialog`. 5 hooks TanStack Query v5. Toasts, skeletons, estado vacío. 247/247 vitest. Fixes post-testing: modal centrado (`m-auto` en `<dialog>`), caché TanStack Query limpiado al logout (`queryClient.clear()`), `ProtectedRoute` no guarda `from` en rutas con `requiredRoles` para evitar redirect a ruta sin permisos tras cambio de usuario.

**Skills**: `tailwind-design-system`, `ui-design-system`, `frontend-state-management`, `vercel-react-best-practices`, `testing-e2e-playwright`
**Dependencias**: `addresses-crud-by-user` ✅, `frontend-layout-components-shared` ✅

---

## EPIC 08 — Carrito de Compras

### ✅ `frontend-shopping-cart-zustand`
Archivado: `2026-05-14-frontend-shopping-cart-zustand`
**Evidencia**: `openspec/changes/archive/2026-05-14-frontend-shopping-cart-zustand/`

CartStore hardening (`ingredientes_excluidos: number[]`, `uiStore` con `cartDrawerOpen`). Feature `features/cart/`: `useCart`, `QuantityStepper`, `CartItemRow`, `EmptyCart`, `OrderSummary`. Widget `CartDrawer` (slide-in, focus trap, Escape, backdrop). `CartPage` lazy-loaded. CartIcon con badge animado en Navbar. 275/275 vitest. Fixes post-testing: theme toggle movido al footer del Sidebar, cart se vacía al logout, redirect a `/login` al hacer checkout sin sesión (CartDrawer + OrderSummary con `state.from` correcto).

**Skills**: `tailwind-design-system`, `ui-design-system`, `zustand-state-management`, `frontend-state-management`, `vercel-react-best-practices`, `testing-e2e-playwright`
**Dependencias**: `frontend-zustand-stores-setup` ✅

---

### ✅ `frontend-shopping-cart-ui`
Archivado: `2026-05-14-frontend-shopping-cart-ui`
**Evidencia**: `openspec/changes/archive/2026-05-14-frontend-shopping-cart-ui/`

Visual upgrade completo del carrito. CartItemRow: imagen 96×96 desktop, fallback con inicial en gradiente brand, pills ingredientes `rounded-full`, animación entrada `slide-in-down`. OrderSummary: desglose Subtotal/Envío/Total, badge "¡Gratis!" (`bg-primary/10`) con umbral $3.000, "Te faltan $X", CTA con total inline. EmptyCart rediseñado con SVG + copy invitador. CartPage 2 columnas desktop / stack mobile con resumen sticky. CartDrawer coherente. 278/278 vitest. 5 specs nuevas sincronizadas.

**Skills**: `tailwind-design-system`, `ui-design-system`, `zustand-state-management`, `frontend-state-management`, `vercel-react-best-practices`, `testing-e2e-playwright`
**Dependencias**: `frontend-shopping-cart-zustand` ✅, `frontend-layout-components-shared` ✅

---

## EPIC 09 — Validaciones Pre-Checkout *(NUEVO en v3.0)*

### ✅ `checkout-pre-validation`
Archivado: `2026-05-15-checkout-pre-validation`
**Evidencia**: `openspec/changes/archive/2026-05-15-checkout-pre-validation/`

`POST /api/v1/pedidos/validar` (CLIENT). Verifica stock disponible, precios vigentes (tolerancia 1¢), productos válidos/disponibles, dirección de entrega existente, carrito no vacío. HTTP 422 RFC 7807 para hard blocks (carrito vacío, sin dirección). HTTP 200 con payload `ValidarCarritoResponse` para soft warnings (stock/precio drift). Frontend: `useCheckoutValidation` hook (useMutation), `CheckoutValidationModal` (hard block vs soft warning), `CheckoutPage` con validación al montar, `/checkout` route. `precio_carrito` congelado en cartStore al primer addItem. 12/12 pytest + 293/293 vitest + 3 E2E Playwright. Bugfix post-apply: `stock_cantidad`/`precio_base` field names.

**Skills**: `python-fastapi-ddd-skill`, `supabase-postgres-best-practices`, `api-design`, `rest-api-design-patterns`, `jwt-security`, `tailwind-design-system`, `frontend-state-management`, `vercel-react-best-practices`, `testing-e2e-playwright`, `post-change-verification`
**Dependencias**: `products-crud-core` ✅, `frontend-shopping-cart-zustand` ✅

---

## EPIC 10 — Pedidos

### ✅ `orders-fsm-backend`
Archivado: `2026-05-15-orders-fsm-backend`
**Evidencia**: `openspec/changes/archive/2026-05-15-orders-fsm-backend/`

FSM 6 estados: PENDIENTE→CONFIRMADO→EN_PREPARACIÓN→EN_CAMINO→ENTREGADO + CANCELADO. `HistorialEstadoPedido` append-only. Snapshot precio + dirección. UoW atómico. Personalización como `INTEGER[]` (RN-PE07). `SELECT FOR UPDATE` para stock (RN-PE04). PENDIENTE→CONFIRMADO solo por Sistema/webhook (RN-FS02). `PedidoRepository` + `HistorialEstadoPedidoRepository`. `VALID_TRANSITIONS` dict + `SYSTEM_ONLY_TARGETS`. 29/29 pytest, 96% coverage.

**Skills**: `python-fastapi-ddd-skill`, `supabase-postgres-best-practices`, `api-design`, `post-change-verification`
**Dependencias**: `backend-patterns-base-repository-uow`, `addresses-crud-by-user`, `products-crud-core`

---

### ✅ `orders-api-endpoints`
Archivado: `2026-05-15-orders-api-endpoints`
**Evidencia**: `openspec/changes/archive/2026-05-15-orders-api-endpoints/`

`POST /api/v1/pedidos` (CLIENT, rate 10/h por usuario_id), `GET /api/v1/pedidos` (paginado), `GET /api/v1/pedidos/{id}` (ownership → 403), `PATCH /api/v1/pedidos/{id}/estado` (ADMIN only), `DELETE /api/v1/pedidos/{id}` (FSM cancel + soft delete atómico). RFC 7807. 28/28 pytest.

**Skills**: `python-fastapi-ddd-skill`, `supabase-postgres-best-practices`, `api-design`, `rest-api-design-patterns`, `jwt-security`, `post-change-verification`
**Dependencias**: `orders-fsm-backend`

---

### ✅ `frontend-orders-listing-ui`
Archivado: `2026-05-15-frontend-orders-listing-ui`
**Evidencia**: `openspec/changes/archive/2026-05-15-frontend-orders-listing-ui/`

MyOrdersPage (`/orders`) — timeline visual CLIENT con OrderCard, badge por estado, skeletons, paginación. OrdersPanelPage (`/admin/pedidos`) — tabla profesional ADMIN/PEDIDOS con filtros por estado/email/fecha. ORDER_STATUS_MAP como Record. Tokens `--color-accent-orange/purple` agregados. Backend: list_all() + count_all() con filtros q/estado/fecha. 314/314 vitest. Fixes post-testing: filtro email backend, nav links, rutas `/orders` y `/orders/:id`.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `zustand-state-management`, `frontend-state-management`, `testing-e2e-playwright`, `dashboard-crud-page`
**Dependencias**: `orders-api-endpoints`, `frontend-layout-components-shared`

---

### ✅ `frontend-orders-detail-ui`
Archivado: `2026-05-16-frontend-orders-detail-ui`
**Evidencia**: `openspec/changes/archive/2026-05-16-frontend-orders-detail-ui/`

Página `/pedidos/:id` y `/admin/pedidos/:id`. OrderDetailHeader (fecha, total, badge, dirección snapshot). OrderItemSnapshot (nombre_snapshot + precio_snapshot, nunca datos vivos). OrderTimeline (slide-in CSS puro, staggered delay). OrderActions (FSM por rol — CLIENT cancela PENDIENTE, ADMIN avanza estados). CancelOrderModal (dialog nativo, focus trap). useOrderDetailStore (Zustand v5). 347/347 vitest. Bugfixes: direccion_snapshot parseada de JSON string, cancel sin soft-delete (pedido queda visible como CANCELADO), es_alergeno renombrado, ProductDetail fetchea GET /productos/:id al abrirse.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `zustand-state-management`, `frontend-state-management`, `testing-e2e-playwright`, `dashboard-crud-page`
**Dependencias**: `orders-api-endpoints`, `frontend-layout-components-shared`

---

### ✅ `frontend-orders-management-admin`
Archivado: `2026-05-16-frontend-orders-management-admin`
**Evidencia**: `openspec/changes/archive/2026-05-16-frontend-orders-management-admin/`

Panel admin completo de gestión de pedidos. OrdersManagementTable (tabla desktop + cards mobile). StateTransitionModal (FSM-aware, solo transiciones válidas). BulkActionsBar (deshabilitado si estados mixtos). BulkConfirmModal (alertdialog). OrderFiltersPanel (totalMin/totalMax collapsible). ordersManagementStore (Set<number> selección bulk). useBulkOrderActions (Promise.allSettled). 430/430 vitest. Fix: email duplicado eliminado de OrderFiltersPanel.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `zustand-state-management`, `frontend-state-management`, `testing-e2e-playwright`, `dashboard-crud-page`
**Dependencias**: `frontend-orders-listing-ui`, `frontend-orders-detail-ui`

---

## EPIC 11 — Pagos

### ✅ `payments-mercadopago-integration-backend`
Archivado: `2026-05-18-payments-mercadopago-integration-backend`
**Evidencia**: `openspec/changes/archive/2026-05-18-payments-mercadopago-integration-backend/`

Módulo `backend/pagos/` completo. `POST /api/v1/pagos/crear-preferencia` (CLIENT, rate 5/min) — crea preferencia MP, retorna `init_point`. `GET /api/v1/pagos/{pedido_id}/status` (CLIENT/ADMIN). `POST /api/v1/webhooks/mercadopago` (público) — valida firma HMAC-SHA256, audit log en `pago_webhook_log`, idempotencia UNIQUE (RN-PA02), `approved`→FSM `confirmar_pedido_por_pago`. `PagoWebhookLog` append-only. Migración 010. `get_mp_sdk()` singleton con `@lru_cache`. 18/18 pytest, 73% coverage. Bugfixes: `auto_return` eliminado (localhost inválido para MP), HTTP status check en webhook (int 404 rompía INSERT), mocks de tests actualizados con `"status": 200`.

**Skills**: `python-fastapi-ddd-skill`, `supabase-postgres-best-practices`, `api-design`, `web-payments`, `post-change-verification`
**Dependencias**: `orders-fsm-backend`

---

### ✅ `frontend-payment-checkout-ui`
Archivado: `2026-05-18-frontend-payment-checkout-ui`
**Evidencia**: `openspec/changes/archive/2026-05-18-frontend-payment-checkout-ui/`

Página `/checkout` completa. `PaymentMethodSelector` (radiogroup ARIA, MercadoPago habilitado, Tarjeta/Efectivo disabled). `MercadoPagoButton` (SDK CDN defer, brickless `mp.checkout({ autoOpen: true })`). `PaymentStatusModal` (success/error/pending). `paymentStore` Zustand v5 sin persist. Hooks: `useCreateOrder`, `useCreatePreference`, `usePaymentStatus`. Detección resultado via query params `?payment=success|failure|pending&pedido_id=X`. Flujo 2 pasos: "Preparar pago" (crea pedido + preferencia) → "Pagar con MercadoPago" (abre modal). 491/491 vitest. Bugfixes post-testing: `setStatus('waiting_payment')` movido a MercadoPagoButton.handleClick (no en onSuccess del hook), selector reactivo `preferenceId` en CheckoutPage, botones mutuamente excluyentes.

**Skills**: `tailwind-design-system`, `ui-design-system`, `vercel-react-best-practices`, `zustand-state-management`, `frontend-state-management`, `testing-e2e-playwright`, `web-payments`
**Dependencias**: `payments-mercadopago-integration-backend`, `addresses-crud-by-user`, `frontend-shopping-cart-zustand`, `checkout-pre-validation`

---

### ✅ `frontend-payment-checkout-fixes`
Archivado: `2026-05-18-frontend-payment-checkout-fixes`
**Evidencia**: `openspec/changes/archive/2026-05-18-frontend-payment-checkout-fixes/`

3 bugfixes post-testing. BUG1: validación teléfono — `replace(/\D/g,'')` antes del regex (números formateados como `+54 11 2345-6789` eran rechazados). BUG2: `onError` en ambas mutations con toast + `setStatus('idle')`, eliminado `aria-hidden` del botón. BUG3: `CartDrawer` retorna null en `/checkout` via `useLocation` (early return después de todos los hooks — Rules of Hooks), `setCartDrawerOpen(false)` al montar CheckoutPage, botón "← Volver al carrito". Hooks-level `onError` ya no sobreescriben status (lo maneja call-site). 491/491 vitest.

**Skills**: `tailwind-design-system`, `ui-design-system`, `frontend-state-management`, `zustand-state-management`
**Dependencias**: `frontend-payment-checkout-ui`

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
├─ ✅ frontend-route-guards-auth
└─ ✅ frontend-error-handling-global

BLOQUE 2 — Layout Base
├─ ✅ frontend-layout-components-shared
├─ ✅ frontend-refactor-apply-skills
└─ ✅ frontend-nav-responsive-fix

BLOQUE 3 — Layout + Catálogo
├─ ✅ categories-crud-hierarchical
├─ ✅ ingredients-crud-allergens
├─ ✅ products-crud-core
├─ ✅ products-categories-association
├─ ✅ products-ingredients-association
├─ ✅ products-catalog-public
└─ ✅ frontend-products-catalog-ui   (INC-01 resuelto 2026-05-13)

BLOQUE 4 — Perfil + Direcciones + Carrito
├─ ✅ backend-user-profile-endpoints
├─ ✅ frontend-user-profile-ui
├─ ✅ addresses-crud-by-user
├─ ✅ frontend-addresses-ui
├─ ✅ frontend-shopping-cart-zustand
└─ ✅ frontend-shopping-cart-ui

BLOQUE 5 — Pre-checkout + Pedidos
├─ ✅ checkout-pre-validation
├─ ✅ orders-fsm-backend
├─ ✅ orders-api-endpoints
├─ ✅ frontend-orders-listing-ui
├─ ❌ frontend-orders-detail-ui
└─ ❌ frontend-orders-management-admin

BLOQUE 6 — Pagos
├─ ✅ payments-mercadopago-integration-backend
├─ ✅ frontend-payment-checkout-ui
├─ ✅ frontend-payment-checkout-fixes
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
| 4.6 | 2026-05-18 | frontend-payment-checkout-fixes archivado. 3 bugfixes: teléfono regex, onError mutations, CartDrawer bloqueado en /checkout. PRÓXIMO: frontend-payment-status-polling. |
| 4.5 | 2026-05-18 | frontend-payment-checkout-ui archivado. CheckoutPage completa + PaymentMethodSelector + MercadoPagoButton + PaymentStatusModal + paymentStore. 491/491 vitest. |
| 4.4 | 2026-05-18 | payments-mercadopago-integration-backend archivado. POST /pagos/crear-preferencia + GET /pagos/{id}/status + POST /webhooks/mercadopago. PagoWebhookLog audit log. HMAC-SHA256 firma. 18/18 pytest. PRÓXIMO: frontend-payment-checkout-ui. |
| 4.3 | 2026-05-16 | frontend-orders-management-admin archivado. Tabla bulk + StateTransitionModal + BulkActionsBar + filtros avanzados. 430/430 vitest. PRÓXIMO: BLOQUE 6 pagos. |
| 4.2 | 2026-05-16 | frontend-orders-detail-ui archivado. OrderDetailPage + OrderTimeline + CancelOrderModal + bugfixes (direccion_snapshot, cancel sin soft-delete, es_alergeno). PRÓXIMO: frontend-orders-management-admin. |
| 4.1 | 2026-05-15 | frontend-orders-listing-ui archivado. MyOrdersPage + OrdersPanelPage. ORDER_STATUS_MAP, filtros email/estado/fecha, tokens accent-orange/purple. 314/314 vitest. PRÓXIMO: frontend-orders-detail-ui. |
| 4.0 | 2026-05-15 | orders-api-endpoints archivado. POST/GET/PATCH/DELETE /api/v1/pedidos. Rate limit por usuario_id, ownership 403, FSM ADMIN-only, soft delete atómico. 28/28 pytest. PRÓXIMO: frontend-orders-listing-ui. |
| 3.9 | 2026-05-15 | orders-fsm-backend archivado. FSM 6 estados, PedidoRepository, HistorialEstadoPedidoRepository, VALID_TRANSITIONS, SELECT FOR UPDATE. 29/29 pytest 96% coverage. PRÓXIMO: orders-api-endpoints. |
| 3.8 | 2026-05-15 | checkout-pre-validation archivado. POST /api/v1/pedidos/validar. Hard block 422/soft warning 200. precio_carrito congelado. PRÓXIMO: orders-fsm-backend. |
| 3.7 | 2026-05-14 | frontend-shopping-cart-ui archivado. Visual upgrade completo: CartItemRow gradiente, OrderSummary desglose + envío gratis, EmptyCart rediseñado, CartPage 2 col. PRÓXIMO: BLOQUE 5 checkout-pre-validation. |
| 3.6 | 2026-05-14 | frontend-shopping-cart-zustand archivado. CartDrawer + CartPage + store hardening. Fixes: theme toggle sidebar, cart clear logout, checkout redirect. PRÓXIMO: frontend-shopping-cart-ui. |
| 3.5 | 2026-05-14 | frontend-addresses-ui archivado. Fixes: modal centrado, queryClient.clear() en logout, ProtectedRoute sin from en rutas con requiredRoles. PRÓXIMO: frontend-shopping-cart-zustand. |
| 3.4 | 2026-05-14 | addresses-crud-by-user archivado. PRÓXIMO: frontend-addresses-ui. |
| 3.3 | 2026-05-14 | frontend-catalog-profile-fixes archivado. 3 nuevas specs: toast-error-normalisation, change-password-form, catalog-filter-ui. |
| 3.2 | 2026-05-13 | INC-01 resuelto. Árbol de bloques sincronizado con estado real. frontend-refactor-apply-skills + frontend-nav-responsive-fix agregados. PRÓXIMO: backend-user-profile-endpoints. |
| 3.1 | 2026-05-11 | Estado real sincronizado con OPSX archive. 6 inconsistencias documentadas (INC-01 a INC-06). BLOQUE 0 de reparación agregado. Nuevos changes: `frontend-widgets-layer`, `frontend-patterns-hooks-optimistic`, `deploy-production`. Corrección naming `es_predeterminada`. `INTEGER[]` explicitado en pedidos. `frontend-products-catalog-ui` marcado ⚠️. |
| 3.0 | 2026-05-11 | Análisis de gaps completo. Changes nuevos: checkout-pre-validation, backend-admin-users-endpoints, system-configuration-backend, frontend-system-configuration-ui. |
| 2.0 | 2026-04-24 | backend-dev-infrastructure agregado |
| 1.0 | 2026-04-21 | Documento inicial |
