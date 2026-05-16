## 0. Skills

- [x] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens semánticos Tailwind v4, variantes CVA, patrones responsive
- [x] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — WCAG AA, ARIA patterns, tabla semántica, checkboxes accesibles
- [x] 0.3 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — re-render optimization, bundle-barrel-imports, rerender-no-inline-components
- [x] 0.4 Leer `.agents/skills/zustand-state-management/README.md` — Zustand v5 create<T>()(), useShallow, selector patterns
- [x] 0.5 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación Zustand (cliente) vs TanStack Query (servidor)
- [x] 0.6 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — loginAs helper, page.route mocks, waitForFunction hidratación Zustand
- [x] 0.7 Leer `.agents/skills/dashboard-crud-page/SKILL.md` — estructura página admin, tabla + modal + confirm dialog patterns

## 1. Análisis previo — backend y código existente

- [x] 1.1 Verificar si `GET /api/v1/pedidos` serializa `usuario_email` en `backend/pedidos/schemas.py` — si no existe, documentar fallback `#usuario_id` en el componente
- [x] 1.2 Leer `frontend/src/features/orders/types/index.ts` — extender interfaz `Order` con `usuario_email?: string | null` si el campo existe en backend
- [x] 1.3 Leer `frontend/src/features/orders/store/ordersFilterStore.ts` — planificar extensión con `totalMin`, `totalMax`, `usuarioEmail`
- [x] 1.4 Leer `frontend/src/features/orders/hooks/useOrders.ts` — verificar qué query params acepta; planificar adición de `totalMin`, `totalMax`, `usuarioEmail`
- [x] 1.5 Leer `frontend/src/features/orders/components/OrdersTable.tsx` y `OrdersFilters.tsx` — entender estructura existente antes de crear componentes nuevos
- [x] 1.6 Leer `frontend/src/features/orders/constants/` — verificar si existe `fsm.ts`; si no, crearlo en la tarea 3.1

## 2. Zustand store — selección y bulk state

- [x] 2.1 Crear `frontend/src/features/orders/store/ordersManagementStore.ts` con: `selectedIds: Set<number>`, `isBulkPending: boolean`, acciones `toggleId(id)`, `setAllIds(ids)`, `clearAll()`, `setIsBulkPending(v)` — Zustand v5 `create<T>()()`
- [x] 2.2 Extender `frontend/src/features/orders/store/ordersFilterStore.ts` agregando `totalMin: number | null`, `totalMax: number | null`, `usuarioEmail: string` con sus setters y `resetFilters` actualizado
- [x] 2.3 Exportar el nuevo store desde `frontend/src/features/orders/store/index.ts` (o crear el archivo si no existe)
- [x] 2.4 Escribir tests unitarios vitest en `frontend/src/features/orders/store/__tests__/ordersManagementStore.test.ts` — cubriendo toggle, setAll, clearAll, indeterminate state derivation

## 3. Constantes FSM

- [x] 3.1 Crear `frontend/src/features/orders/constants/fsm.ts` con `FSM_TRANSITIONS: Record<number, number[]>` y `ORDER_STATUS_LABELS: Record<number, string>` (mapeo id → label legible en español) — usar los mismos valores que `OrderStatusBadge`
- [x] 3.2 Crear función helper `getValidTransitions(currentStatusId: number): number[]` en `fsm.ts` — retorna array vacío para estados terminales (5, 6)
- [x] 3.3 Crear función helper `isTerminalState(statusId: number): boolean` en `fsm.ts`

## 4. Componente StateTransitionModal

- [x] 4.1 Crear `frontend/src/features/orders/components/StateTransitionModal.tsx` — props: `orderId`, `currentStatusId`, `isOpen`, `onClose`, `onSuccess`; usa `getValidTransitions` de `fsm.ts`
- [x] 4.2 Implementar renderizado condicional: si `isTerminalState(currentStatusId)` → mostrar mensaje "Este pedido está en estado terminal" sin radio inputs
- [x] 4.3 Renderizar radio inputs (`<input type="radio">`) para cada transición válida con label legible (`ORDER_STATUS_LABELS`)
- [x] 4.4 Conectar submit al hook `useAdvanceOrderState` — disabled si ningún estado seleccionado o si `mutation.isPending`
- [x] 4.5 Mostrar error de API en el modal (inline, no toast) si la mutación falla; toast de éxito si tiene éxito (usar `useUIStore.addToast`)
- [x] 4.6 Implementar variante bulk: prop `isBulkMode?: boolean; bulkOrderIds?: number[]` — en bulk mode, el submit itera los IDs con `Promise.allSettled` y muestra resumen
- [x] 4.7 Accesibilidad: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap al abrir, Escape para cerrar
- [x] 4.8 Aplicar solo tokens semánticos Tailwind v4 (`text-foreground`, `bg-muted`, `border-border`, etc.) — cero colores crudos

## 5. Componente BulkActionsBar

- [x] 5.1 Crear `frontend/src/features/orders/components/BulkActionsBar.tsx` — lee `selectedIds` de `ordersManagementStore`; no renderiza si `selectedIds.size === 0`
- [x] 5.2 Mostrar counter "X pedidos seleccionados" — actualización reactiva vía selector granular de Zustand
- [x] 5.3 Implementar botón "Cancelar seleccionados" — abre confirm dialog interno antes de ejecutar
- [x] 5.4 Implementar botón "Cambiar estado masivo" — disabled con tooltip si los pedidos seleccionados tienen estados mixtos; abre `StateTransitionModal` en bulk mode si todos comparten el mismo estado
- [x] 5.5 Confirm dialog para bulk cancel: mostrar "¿Cancelar X pedidos?" con botones "Confirmar" / "Cancelar"; al confirmar ejecutar `Promise.allSettled` de `useCancelOrder` mutations y mostrar toast de resumen
- [x] 5.6 Lógica de detección de estado mixto: derivar `sharedStatusId: number | null` con `useMemo` desde `selectedIds` + `ordersData` — si `null`, deshabilitar "Cambiar estado masivo"
- [x] 5.7 Accesibilidad: `role="toolbar"`, `aria-label="Acciones para pedidos seleccionados"`, `aria-disabled` en botones deshabilitados con mensaje descriptivo

## 6. Componente OrderFiltersPanel

- [x] 6.1 Crear `frontend/src/features/orders/components/OrderFiltersPanel.tsx` — campos adicionales: `usuarioEmail` (text input), `totalMin` (number input), `totalMax` (number input)
- [x] 6.2 Conectar cada campo al `ordersFilterStore` extendido con sus setters correspondientes
- [x] 6.3 Implementar sección colapsable (botón toggle o `<details>`) — "Filtros avanzados" — colapsada por defecto
- [x] 6.4 Botón "Limpiar filtros" que llama a `resetFilters()` del store (ahora incluye los nuevos campos)
- [x] 6.5 Accesibilidad: `<label>` explícito por `htmlFor` en cada input, `aria-label` descriptivo, mensajes de error para rango inválido (min > max)
- [x] 6.6 Aplicar tokens semánticos Tailwind v4 para inputs y labels

## 7. Componente OrdersManagementTable

- [x] 7.1 Crear `frontend/src/features/orders/components/OrdersManagementTable.tsx` — extiende las props de `OrdersTable` con: `onStateChange: (orderId: number) => void`
- [x] 7.2 Agregar columna 0 — checkbox por fila: lee `selectedIds` de `ordersManagementStore`, llama `toggleId(order.id)` al hacer click; `aria-label="Seleccionar pedido #X"`, `aria-checked` refleja estado
- [x] 7.3 Agregar header checkbox (col 0) con lógica indeterminate: `useEffect` que setea `ref.current.indeterminate = selectedIds.size > 0 && selectedIds.size < orders.length`; click llama `setAllIds` o `clearAll`
- [x] 7.4 Agregar columna "Usuario" — muestra `order.usuario_email ?? #${order.usuario_id}`; `scope="col"` en `<th>`
- [x] 7.5 Agregar botón "Cambiar estado" en columna Acciones — calls `onStateChange(order.id)`; `aria-label="Cambiar estado del pedido #X"`; disabled si `isTerminalState(order.estado_pedido_id)` con tooltip "Estado terminal"
- [x] 7.6 Mantener `aria-selected` en cada `<tr>` reflejando si el pedido está en `selectedIds`; `role="row"` en `<tr>`; `role="grid"` en `<table>`
- [x] 7.7 Skeleton rows en `isLoading` — reutilizar `OrdersSkeleton` con columna extra para checkbox y usuario
- [x] 7.8 Responsive: envolver tabla en `<div className="hidden md:block">` y renderizar lista de `OrderCard` en `<div className="block md:hidden">`

## 8. Integración en OrdersPanelPage / OrdersManagementPage

- [x] 8.1 Crear `frontend/src/pages/OrdersManagementPage.tsx` (o extender `OrdersPanelPage.tsx`) — importar `OrdersManagementTable`, `BulkActionsBar`, `OrderFiltersPanel`, `StateTransitionModal`
- [x] 8.2 Añadir estado local `stateModalOrderId: number | null` para controlar qué pedido tiene el modal abierto
- [x] 8.3 Pasar `onStateChange={(id) => setStateModalOrderId(id)}` a `OrdersManagementTable`
- [x] 8.4 Renderizar `<StateTransitionModal>` condicionalmente cuando `stateModalOrderId !== null` — pasar `currentStatusId` del pedido correspondiente (lookup en `data.items`)
- [x] 8.5 Renderizar `<BulkActionsBar>` sobre o bajo la tabla — pasar `orders={data?.items ?? []}` para detección de estado mixto
- [x] 8.6 Renderizar `<OrderFiltersPanel>` debajo de `OrdersFilters` existente (o reemplazarlo si se decide unificar)
- [x] 8.7 Actualizar `frontend/src/app/Router.tsx` — si se creó `OrdersManagementPage.tsx`, reemplazar el lazy import de `OrdersPanelPage` por el nuevo componente en la ruta `/admin/pedidos`
- [x] 8.8 Verificar que `clearAll()` del `ordersManagementStore` se llame al cambiar de página (useEffect con `page` como dep)
- [x] 8.9 Pasar `ordersData` al `BulkActionsBar` para derivar `sharedStatusId`

## 9. Tests unitarios vitest

- [x] 9.1 Crear `frontend/src/features/orders/components/__tests__/StateTransitionModal.test.tsx` — testear: renders solo transiciones válidas, terminal state message, submit deshabilitado sin selección, mock de `useAdvanceOrderState`
- [x] 9.2 Crear `frontend/src/features/orders/components/__tests__/BulkActionsBar.test.tsx` — testear: no renderiza con `selectedIds` vacío, counter correcto, botón bulk state disabled con estados mixtos
- [x] 9.3 Crear `frontend/src/features/orders/components/__tests__/OrdersManagementTable.test.tsx` — testear: checkbox toggle, header indeterminate, columna usuario con email y con fallback
- [x] 9.4 Agregar tests de `getValidTransitions` y `isTerminalState` en `frontend/src/features/orders/constants/__tests__/fsm.test.ts`

## 10. Tests E2E Playwright

- [x] 10.1 Crear `frontend/e2e/admin/orders-management.spec.ts` — setup: `loginAs(page, 'ADMIN')`, mock `GET /api/v1/pedidos` con fixture de 5 pedidos en estados variados
- [x] 10.2 Test: filtrar por estado — mock retorna pedidos CONFIRMADO, verificar que tabla muestra solo esos
- [x] 10.3 Test: seleccionar un pedido → BulkActionsBar aparece con "1 pedido seleccionado"
- [x] 10.4 Test: seleccionar todos → header checkbox checked, counter = 5
- [x] 10.5 Test: cambiar estado de un pedido — click "Cambiar estado", modal abre con opciones correctas, seleccionar opción, confirmar, mock PATCH 200, verificar toast éxito
- [x] 10.6 Test: bulk cancel — seleccionar 2 pedidos, click "Cancelar seleccionados", confirm dialog aparece, confirmar, mock DELETE 200 × 2, verificar toast "2 pedidos cancelados"
- [x] 10.7 Test: guard rol CLIENT → `/admin/pedidos` redirige a `/403` (reutilizar patrón de `testing-e2e-playwright` skill)
- [x] 10.8 Test: filtros avanzados — ingresar email, verificar que query param `q=email` aparece en la petición interceptada

## 11. Verificación final

- [x] 11.1 Correr `cd frontend && npx vitest run` — todos los tests pasan, coverage de nuevos archivos ≥ 40%
- [x] 11.2 Correr `npm run lint` en frontend — sin errores TypeScript strict
- [x] 11.3 Correr `npx tsc --noEmit` — sin errores de tipos
- [x] 11.4 Verificar en browser: desktop muestra tabla, mobile (< 768px) muestra cards
- [x] 11.5 Verificar accesibilidad: tab navigation a través de la tabla, checkboxes, botones de acción; sin trampas de foco fuera de modales
- [x] 11.6 Correr `npx playwright test e2e/admin/orders-management.spec.ts` — todos los tests E2E pasan
- [x] 11.7 Confirmar que no hay colores crudos en los nuevos componentes — solo tokens semánticos Tailwind v4
