## Why

Los usuarios CLIENT no tienen ninguna pantalla para consultar el historial de sus pedidos, y los operadores ADMIN/PEDIDOS carecen de un panel centralizado para gestionar pedidos en curso. El backend `orders-api-endpoints` (archivado en b09bc7a) ya expone `GET /api/v1/pedidos` con paginación; este change cierra la brecha entre la API disponible y la experiencia de usuario final.

## What Changes

- Nuevo feature `frontend/src/features/orders/` con tipos TypeScript, hook TanStack Query y componentes compartidos.
- Nueva página `/mis-pedidos` (`MyOrdersPage`) — vista timeline para usuarios CLIENT: tarjetas de pedido con badge de estado semántico, skeletons, estado vacío y paginación.
- Nueva página `/admin/pedidos` (`OrdersPanelPage`) — tabla profesional para roles ADMIN/PEDIDOS: columnas de datos, filtros por estado/fecha/usuario, skeletons de tabla, paginación y acciones de fila.
- Componente compartido `OrderCard` — reutilizable en ambas vistas mediante prop `mode: "client" | "admin"`.
- Componente `OrderStatusBadge` — badge semántico por estado (PENDIENTE, CONFIRMADO, EN_PREPARACIÓN, EN_CAMINO, ENTREGADO, CANCELADO) usando tokens `@theme` de Tailwind v4.
- Componente `OrdersTable` — tabla ARIA-compliant con `role="table"` para la vista admin.
- Componente `OrdersFilters` — filtros de UI gestionados con Zustand v5 (estado cliente).
- Componente `OrdersSkeleton` — skeletons de carga para ambas vistas.
- Tests unitarios con vitest para OrderCard, skeletons y estados vacíos.
- Tests E2E con Playwright para listar pedidos, filtrar por estado, paginar y validar diferencia por rol.
- Rutas registradas en el router de la app con `React.lazy` + `Suspense`.

## Capabilities

### New Capabilities

- `orders-listing`: Listado de pedidos paginado para usuarios CLIENT vía vista timeline (`/mis-pedidos`) y para ADMIN/PEDIDOS vía panel de tabla (`/admin/pedidos`). Incluye hook `useOrders`, componentes compartidos `OrderCard`/`OrderStatusBadge`, filtros de UI con Zustand y cobertura de tests vitest + Playwright.

### Modified Capabilities

<!-- No hay specs existentes afectadas. El backend de pedidos ya fue especificado en orders-fsm-backend y orders-api-endpoints; este change solo consume la API, no la modifica. -->

## Impact

- **Frontend**: nuevos archivos bajo `frontend/src/features/orders/`, `frontend/src/pages/MyOrdersPage.tsx`, `frontend/src/pages/OrdersPanelPage.tsx`, `frontend/src/e2e/orders-listing.spec.ts`.
- **Router**: agregar rutas `/mis-pedidos` (guard CLIENT) y `/admin/pedidos` (guard ADMIN | PEDIDOS) en el router principal.
- **Dependencias**: ninguna nueva — TanStack Query v5, Zustand v5, Axios y Tailwind v4 ya están instalados. Playwright ya está o se instala según skill `testing-e2e-playwright`.
- **Backend**: solo lectura vía `GET /api/v1/pedidos` — sin cambios al backend.
- **API consumida**: `GET /api/v1/pedidos?limit=N&offset=N` → `{ items, total, limit, offset }`.
