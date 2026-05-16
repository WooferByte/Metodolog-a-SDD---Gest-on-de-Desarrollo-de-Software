## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens `@theme` v4, CVA, responsive mobile-first para OrderCard y badges de estado
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — ARIA, WCAG AA, composición de componentes accesibles (`role="table"`, `aria-label`, `aria-current`)
- [ ] 0.3 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — `React.lazy`, bundle splitting, `keepPreviousData`, re-render optimization
- [ ] 0.4 Leer `.agents/skills/zustand-state-management/README.md` — Zustand v5 store tipado `create<T>()()` para filtros UI del panel admin
- [ ] 0.5 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación TanStack Query (server) vs Zustand (client), nunca duplicar datos de servidor
- [ ] 0.6 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — `loginAs()`, `page.route()`, `addInitScript`, espera hidratación Zustand
- [ ] 0.7 Leer `.agents/skills/dashboard-crud-page/SKILL.md` — patrones de tabla admin con skeletons, paginación, columnas con `useMemo`

## 1. Verificación de contexto y tokens de color

- [ ] 1.1 Verificar que `frontend/src/app/` (o equivalente) define un `@theme` con tokens semánticos de color — buscar `globals.css`, `index.css` o `app.css`
- [ ] 1.2 Si no existen, agregar tokens necesarios al CSS base: `--color-warning`, `--color-success`, `--color-info`, `--color-accent-orange`, `--color-accent-purple` con valores OKLCH apropiados
- [ ] 1.3 Verificar respuesta real de `GET /api/v1/pedidos` (curl o Swagger) para confirmar estructura de campo `estado_pedido_id` y si el backend filtra por usuario JWT automáticamente para rol CLIENT (resolver OQ-1)
- [ ] 1.4 Verificar que el router principal (`@/app/router.tsx` o equivalente) tiene estructura para agregar rutas protegidas por rol — identificar el componente `ProtectedRoute` existente

## 2. Tipos y constantes del feature orders

- [ ] 2.1 Crear `frontend/src/features/orders/types/index.ts` con interfaces: `Order` (id, usuario_id, estado_pedido_id, total, creado_en, observacion, direccion_snapshot, forma_pago_id), `OrdersPage` (items, total, limit, offset), `OrderStatusMeta` (id, label, colorClass)
- [ ] 2.2 Crear `frontend/src/features/orders/constants/orderStatus.ts` con `ORDER_STATUS_MAP: Record<number, OrderStatusMeta>` mapeando IDs 1–6 a labels y clases de color semántico Tailwind v4

## 3. Hook TanStack Query — useOrders

- [ ] 3.1 Crear `frontend/src/features/orders/hooks/useOrders.ts` — hook `useOrders({ limit, offset, estadoId?, search?, fechaDesde?, fechaHasta? })` usando `useQuery` de TanStack Query v5
- [ ] 3.2 Configurar `placeholderData: keepPreviousData` en `useQuery` para evitar flash en paginación
- [ ] 3.3 El hook debe llamar a `GET /api/v1/pedidos` vía el cliente Axios de `@/shared/api/axios` con los query params correspondientes
- [ ] 3.4 El tipo de retorno debe ser `UseQueryResult<OrdersPage>` con tipado estricto TypeScript

## 4. Store Zustand — filtros del panel admin

- [ ] 4.1 Crear `frontend/src/features/orders/store/useOrdersFilterStore.ts` con `create<OrdersFilterState>()()` en Zustand v5 — estado: `estadoId: number | null`, `search: string`, `fechaDesde: string`, `fechaHasta: string`
- [ ] 4.2 Agregar acciones: `setEstadoId`, `setSearch`, `setFechaDesde`, `setFechaHasta`, `resetFilters` — nunca almacenar datos del servidor en este store

## 5. Componente OrderStatusBadge

- [ ] 5.1 Crear `frontend/src/features/orders/components/OrderStatusBadge.tsx` — recibe `statusId: number`, consulta `ORDER_STATUS_MAP`, renderiza `<span>` con clase de color semántico y texto de estado
- [ ] 5.2 Manejar el caso de `statusId` desconocido con fallback "DESCONOCIDO" y clase `text-muted-foreground`
- [ ] 5.3 Agregar `aria-label="Estado del pedido: <label>"` al span del badge

## 6. Componente OrdersSkeleton

- [ ] 6.1 Crear `frontend/src/features/orders/components/OrdersSkeleton.tsx` — recibe `mode: "client" | "admin"` y `count: number`
- [ ] 6.2 En modo `"client"`: renderizar N tarjetas skeleton con `animate-pulse` usando tokens semánticos, con forma aproximada de OrderCard (header, body con líneas, footer)
- [ ] 6.3 En modo `"admin"`: renderizar N filas skeleton dentro de `<tbody>` con celdas de ancho correspondiente a las columnas de la tabla

## 7. Componente OrderCard

- [ ] 7.1 Crear `frontend/src/features/orders/components/OrderCard.tsx` — props: `order: Order`, `mode: "client" | "admin"`, `onViewDetail?: (id: number) => void`
- [ ] 7.2 Modo `"client"`: renderizar tarjeta timeline con `OrderStatusBadge`, fecha formateada (`creado_en`), total formateado en ARS y botón "Ver detalle" con `aria-label="Ver detalle del pedido #<id>"`
- [ ] 7.3 Modo `"admin"`: renderizar formato compacto adecuado para uso dentro de `<td>` de tabla
- [ ] 7.4 Aplicar clases Tailwind v4 con tokens semánticos únicamente — cero colores hardcodeados
- [ ] 7.5 Mobile-first: en modo `"client"`, asegurar que el card es readable en viewport 375px sin overflow horizontal

## 8. Componente OrdersTable (vista admin)

- [ ] 8.1 Crear `frontend/src/features/orders/components/OrdersTable.tsx` — tabla semántica con `<table role="table">`, `<thead>`, `<tbody>`, `<th scope="col">`
- [ ] 8.2 Columnas: Email usuario, Fecha, Total (ARS), Estado (`OrderStatusBadge`), Acciones (botón "Ver detalle")
- [ ] 8.3 Estado vacío: cuando `items.length === 0`, mostrar una `<tr>` con `<td colSpan={5}>` y mensaje "No hay pedidos registrados"
- [ ] 8.4 Props: `orders: Order[]`, `isLoading: boolean`, `onViewDetail: (id: number) => void` — cuando `isLoading=true`, renderizar `<OrdersSkeleton mode="admin" count={5} />`

## 9. Componente OrdersFilters (vista admin)

- [ ] 9.1 Crear `frontend/src/features/orders/components/OrdersFilters.tsx` — lee y escribe en `useOrdersFilterStore`
- [ ] 9.2 Campos: select de estado (opciones de `ORDER_STATUS_MAP` + "Todos"), input de búsqueda por email (`aria-label="Buscar por email de usuario"`), inputs de fecha desde/hasta
- [ ] 9.3 Botón "Limpiar filtros" que llama a `resetFilters()` del store
- [ ] 9.4 Todos los inputs deben tener `aria-label` descriptivo y `id` con `htmlFor` en el `<label>` correspondiente

## 10. Página MyOrdersPage (CLIENT)

- [ ] 10.1 Crear `frontend/src/pages/MyOrdersPage.tsx` — página de timeline de pedidos para rol CLIENT
- [ ] 10.2 Usar `useOrders({ limit: 10, offset: page * 10 })` — estado de página local con `useState` para el offset (es UI state de paginación, no server state)
- [ ] 10.3 Mientras `isLoading`: renderizar `<OrdersSkeleton mode="client" count={5} />`
- [ ] 10.4 Cuando `items.length === 0`: renderizar estado vacío con mensaje "No tenés pedidos todavía" y enlace al catálogo `<Link to="/productos">Ir al catálogo</Link>`
- [ ] 10.5 Renderizar lista de `<OrderCard mode="client" order={o} onViewDetail={id => navigate('/mis-pedidos/' + id)} />` en columna única mobile / 2 columnas tablet+
- [ ] 10.6 Paginación con botones Anterior/Siguiente con `aria-current="page"` en el número activo — respetar `total` devuelto por la API
- [ ] 10.7 `isFetching` indicator sutil (borde pulsante o texto "Actualizando...") cuando TanStack Query está re-fetching en background

## 11. Página OrdersPanelPage (ADMIN / PEDIDOS)

- [ ] 11.1 Crear `frontend/src/pages/OrdersPanelPage.tsx` — panel de gestión de pedidos para roles ADMIN/PEDIDOS
- [ ] 11.2 Leer filtros del `useOrdersFilterStore` y pasarlos como query params a `useOrders`
- [ ] 11.3 Renderizar `<OrdersFilters />` encima de la tabla
- [ ] 11.4 Renderizar `<OrdersTable orders={data?.items ?? []} isLoading={isLoading} onViewDetail={...} />`
- [ ] 11.5 Paginación debajo de la tabla con `aria-current="page"` y botones Anterior/Siguiente deshabilitados en los extremos
- [ ] 11.6 `isFetching` indicator visible mientras hay re-fetch (misma estrategia que MyOrdersPage)

## 12. Registro de rutas en el router principal

- [ ] 12.1 Importar páginas con `React.lazy`: `const MyOrdersPage = React.lazy(() => import('@/pages/MyOrdersPage'))` y lo mismo para `OrdersPanelPage`
- [ ] 12.2 Envolver con `Suspense` usando como `fallback` el skeleton correspondiente (`<OrdersSkeleton mode="client" count={5} />` para MyOrders, skeleton admin para OrdersPanel)
- [ ] 12.3 Registrar ruta `/mis-pedidos` bajo `ProtectedRoute` con guard de rol CLIENT
- [ ] 12.4 Registrar ruta `/admin/pedidos` bajo `ProtectedRoute` con guard de roles ADMIN | PEDIDOS

## 13. Tests unitarios — vitest

- [ ] 13.1 Crear `frontend/src/features/orders/components/__tests__/OrderCard.test.tsx` — test que renderiza `<OrderCard mode="client" order={mockOrder} />` y verifica badge, fecha y total en el DOM
- [ ] 13.2 Agregar test de `OrderCard` en modo `"admin"` verificando estructura compacta
- [ ] 13.3 Crear `frontend/src/features/orders/components/__tests__/OrdersSkeleton.test.tsx` — test que verifica que se renderizan N elementos skeleton según prop `count`
- [ ] 13.4 Crear test de estado vacío: mockear `useOrders` retornando `{ data: { items: [], total: 0 } }` y verificar que el mensaje "No tenés pedidos todavía" está en el DOM
- [ ] 13.5 Crear `frontend/src/features/orders/components/__tests__/OrderStatusBadge.test.tsx` — tests para IDs 1, 5, 6 y un ID desconocido (ej. 99)
- [ ] 13.6 Ejecutar `npx vitest run` desde `frontend/` y confirmar ≥ 40% de cobertura del feature `orders`

## 14. Tests E2E — Playwright

- [ ] 14.1 Verificar que Playwright está instalado en `frontend/` (`@playwright/test`); si no, instalarlo con `npm install -D @playwright/test && npx playwright install chromium`
- [ ] 14.2 Crear `frontend/src/e2e/orders/orders-listing.spec.ts` (o en `frontend/e2e/orders/`) siguiendo la estructura del proyecto Playwright existente
- [ ] 14.3 Test: CLIENT navega a `/mis-pedidos` — usar `loginAs(page, 'CLIENT')` + `page.route('**/api/v1/pedidos*', ...)` con respuesta mockeada de 2 pedidos → verificar que hay 2 OrderCard visibles o el mensaje de vacío
- [ ] 14.4 Test: ADMIN navega a `/admin/pedidos` — usar `loginAs(page, 'ADMIN')` → verificar que la tabla con `role="table"` es visible
- [ ] 14.5 Test: CLIENT intenta `/admin/pedidos` → verificar redirect a `/403`
- [ ] 14.6 Test: PEDIDOS accede a `/admin/pedidos` → verificar acceso correcto (sin redirect)
- [ ] 14.7 Test: filtro por estado en panel admin — mockear respuesta filtrada → verificar que la tabla muestra datos actualizados
- [ ] 14.8 Test: paginación avanza → verificar que se llama al endpoint con el offset correcto (usando `page.route` para interceptar)
- [ ] 14.9 Ejecutar `npx playwright test e2e/orders/orders-listing.spec.ts` y confirmar que todos los tests pasan

## 15. Verificación final

- [ ] 15.1 Ejecutar `npx tsc --noEmit` desde `frontend/` y confirmar cero errores TypeScript
- [ ] 15.2 Ejecutar `npx vitest run` desde `frontend/` y confirmar todos los tests unitarios pasan
- [ ] 15.3 Levantar backend (`uvicorn main:app --reload`) y frontend (`npm run dev`), navegar a `/mis-pedidos` como CLIENT y verificar manualmente que el flujo funciona end-to-end
- [ ] 15.4 Navegar a `/admin/pedidos` como ADMIN y verificar filtros, paginación y tabla
- [ ] 15.5 Verificar en mobile (viewport 375px en DevTools) que las OrderCard no tienen overflow horizontal
- [ ] 15.6 Verificar accesibilidad con Tab navigation en ambas páginas — los badges, botones y paginación deben ser alcanzables por teclado con focus ring visible
- [ ] 15.7 Leer `.agents/skills/post-change-verification/SKILL.md` y ejecutar el health check completo antes de proceder al `opsx:archive`
