## 0. Skills

- [x] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens semánticos `@theme`, animaciones `@keyframes`, responsive mobile-first
- [x] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — modal ARIA con Radix Dialog, WCAG AA, keyboard navigation
- [x] 0.3 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — lazy loading, no barrel imports, re-render optimization
- [x] 0.4 Leer `.agents/skills/zustand-state-management/README.md` — patrones store v5 con `create<T>()()`, selectors granulares
- [x] 0.5 Leer `.agents/skills/frontend-state-management/SKILL.md` — TanStack Query v5 para server state, Zustand SOLO para UI state
- [x] 0.6 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — `loginAs()` con `addInitScript`, `page.route()` para mockear FastAPI
- [x] 0.7 Leer `.agents/skills/dashboard-crud-page/SKILL.md` — patrones ConfirmDialog con ARIA, `aria-label` en botones icono

## 1. Tipos TypeScript

- [x] 1.1 Extender `frontend/src/features/orders/types/index.ts` con `OrderDetailItem` (campos: `id`, `producto_id`, `nombre_snapshot`, `cantidad`, `precio_snapshot`, `personalizacion: number[]`)
- [x] 1.2 Extender `frontend/src/features/orders/types/index.ts` con `OrderHistorialItem` (campos: `id`, `estado_anterior_id: number | null`, `estado_nuevo_id`, `usuario_responsable_id`, `usuario_email: string | null`, `creado_en`)
- [x] 1.3 Extender `frontend/src/features/orders/types/index.ts` con `OrderDetail` que extiende `Order` y añade `detalles: OrderDetailItem[]` e `historial: OrderHistorialItem[]`

## 2. Store Zustand para UI del detalle

- [x] 2.1 Crear `frontend/src/features/orders/store/orderDetailStore.ts` con `useOrderDetailStore` (estado: `isCancelModalOpen`, acciones: `openCancelModal`, `closeCancelModal`) usando `create<OrderDetailState>()()`
- [x] 2.2 Verificar que el store NO almacena datos del pedido — solo estado de UI modal (los datos de pedido vienen de TanStack Query)

## 3. Hooks TanStack Query

- [x] 3.1 Crear `frontend/src/features/orders/hooks/useOrderDetail.ts` — `useQuery<OrderDetail>` sobre `GET /api/v1/pedidos/{id}`, query key `['order-detail', id]`, `staleTime: 1000 * 60 * 2`, `retry: 1`
- [x] 3.2 Crear `frontend/src/features/orders/hooks/useCancelOrder.ts` — `useMutation` sobre `DELETE /api/v1/pedidos/{id}`, en `onSuccess`: cerrar modal (via `useOrderDetailStore`), mostrar toast "Pedido cancelado correctamente", invalidar queries `['orders']` y `['order-detail', id]`
- [x] 3.3 Crear `frontend/src/features/orders/hooks/useAdvanceOrderState.ts` — `useMutation` sobre `PATCH /api/v1/pedidos/{id}/estado` con body `{ nuevo_estado_id: number }`, en `onSuccess`: mostrar toast "Estado actualizado", invalidar queries `['orders']` y `['order-detail', id]`
- [x] 3.4 Verificar el campo exacto del body de `PATCH /api/v1/pedidos/{id}/estado` leyendo `backend/pedidos/schemas.py` (campo `nuevo_estado_id` vs `estado_id`)

## 4. Verificación de dependencias

- [x] 4.1 Verificar que `@radix-ui/react-dialog` está en `frontend/package.json` (como dependencia directa); si no, añadirlo
- [x] 4.2 Verificar que el token `--animate-slide-in` con `@keyframes slide-in` existe en el CSS base (`frontend/src/index.css` o equivalente); si no, añadirlo con: `from { transform: translateY(-0.5rem); opacity: 0; } to { transform: translateY(0); opacity: 1; }`

## 5. Componente OrderDetailHeader

- [x] 5.1 Crear `frontend/src/features/orders/components/detail/OrderDetailHeader.tsx` con props `order: OrderDetail`
- [x] 5.2 Mostrar: número de pedido (`#id`), fecha formateada con `Intl.DateTimeFormat` en español-AR, total formateado con `Intl.NumberFormat` en pesos argentinos, `OrderStatusBadge` reutilizado del listing
- [x] 5.3 Mostrar dirección de entrega desde `order.direccion_snapshot` con fallback "Dirección no disponible" si es null
- [x] 5.4 Aplicar responsive mobile-first: stack vertical en mobile, layout horizontal en `md:` y superior

## 6. Componente OrderItemSnapshot

- [x] 6.1 Crear `frontend/src/features/orders/components/detail/OrderItemSnapshot.tsx` con props `item: OrderDetailItem`
- [x] 6.2 Mostrar `nombre_snapshot` (nombre congelado), `cantidad`, `precio_snapshot` formateado en pesos argentinos, subtotal (`cantidad * precio_snapshot`)
- [x] 6.3 Si `personalizacion` es array no vacío: mostrar sección "Personalizaciones" con los IDs como fallback "Ingrediente #ID" (no hacer request adicional a la API de productos)
- [x] 6.4 Si `personalizacion` es vacío o null: no renderizar sección de personalización
- [x] 6.5 Garantizar que NO se hace ninguna request adicional a `GET /api/v1/productos/{id}` desde este componente

## 7. Componente OrderTimeline

- [x] 7.1 Crear `frontend/src/features/orders/components/detail/OrderTimeline.tsx` con props `historial: OrderHistorialItem[]`
- [x] 7.2 Ordenar items por `creado_en` ascendente (el más antiguo primero)
- [x] 7.3 Cada ítem muestra: badge del `estado_nuevo_id` (reutilizando `OrderStatusBadge`), timestamp formateado con fecha y hora en español-AR, email del usuario responsable o fallback "Sistema" si `usuario_email` es null
- [x] 7.4 Aplicar animación de entrada `slide-in` con `animation-delay` inline de `${index * 0.1}s` para escalonar la aparición de cada ítem
- [x] 7.5 Añadir `aria-hidden="true"` a los elementos decorativos del timeline (línea vertical, círculos conectores)
- [x] 7.6 Garantizar que todos los textos de contenido son legibles por screen readers (sin `aria-hidden` en textos de estado o timestamps)

## 8. Componente CancelOrderModal

- [x] 8.1 Crear `frontend/src/features/orders/components/detail/CancelOrderModal.tsx` usando `@radix-ui/react-dialog` primitivo
- [x] 8.2 Implementar `Dialog.Root` con `open={isCancelModalOpen}` y `onOpenChange` conectado a `closeCancelModal` del store
- [x] 8.3 Añadir `Dialog.Title` con id referenciado en `aria-labelledby`, `Dialog.Description` con id referenciado en `aria-describedby`
- [x] 8.4 Botón "Sí, cancelar" llama a `cancelOrder(orderId)` de `useCancelOrder`; mostrar estado de loading con `isPending`
- [x] 8.5 Botón "No, mantener pedido" llama a `closeCancelModal`; ambos botones son alcanzables con Tab
- [x] 8.6 Verificar que `Dialog.Content` incluye `aria-modal="true"` (Radix lo añade automáticamente, pero confirmar en testing)
- [x] 8.7 Verificar que Escape cierra el modal sin ejecutar la cancelación

## 9. Componente OrderActions

- [x] 9.1 Crear `frontend/src/features/orders/components/detail/OrderActions.tsx` con props `order: OrderDetail`, `adminMode?: boolean`
- [x] 9.2 Lógica CLIENT: mostrar botón "Cancelar pedido" siempre visible; habilitado solo si `estado_pedido_id === 1` (PENDIENTE); si disabled, añadir `aria-disabled="true"` y `title="El pedido no puede cancelarse en este estado"`
- [x] 9.3 Al hacer click en "Cancelar pedido" (enabled): llamar a `openCancelModal()` del store
- [x] 9.4 Lógica ADMIN/PEDIDOS (`adminMode=true`): mostrar selector de siguiente estado según la matriz FSM; opciones disponibles calculadas desde `estado_pedido_id` actual usando la constante `VALID_TRANSITIONS` importada de `features/orders/constants/`
- [x] 9.5 Crear constante `VALID_TRANSITIONS: Record<number, number[]>` en `frontend/src/features/orders/constants/orderTransitions.ts` reflejando la matriz FSM del spec
- [x] 9.6 Para estados terminales (5 o 6): mostrar mensaje "Este pedido está cerrado" sin botones de acción
- [x] 9.7 El botón de avanzar estado llama a `advanceState({ orderId, nuevoEstadoId })` de `useAdvanceOrderState`; mostrar loading durante la mutación

## 10. Componente OrderDetailSkeleton

- [x] 10.1 Crear `frontend/src/features/orders/components/detail/OrderDetailSkeleton.tsx` — skeleton con la forma del layout de detalle (header, 3 filas de items, 3 ítems de timeline)
- [x] 10.2 Usar clases Tailwind v4 `animate-pulse` con `bg-muted` para las áreas de skeleton
- [x] 10.3 Añadir `aria-hidden="true"` al skeleton completo y un `sr-only` con "Cargando detalle del pedido"

## 11. Página OrderDetailPage

- [x] 11.1 Crear `frontend/src/pages/OrderDetailPage.tsx` con props `adminMode?: boolean`
- [x] 11.2 Obtener `id` de `useParams()` de react-router-dom; parsear a número con validación (si no es número válido, navegar a 404)
- [x] 11.3 Usar `useOrderDetail(id)` para datos; mientras `isLoading`: mostrar `OrderDetailSkeleton`; si `isError`: mostrar estado de error con CTA "Volver a mis pedidos"
- [x] 11.4 Componer la página: `OrderDetailHeader` + lista de `OrderItemSnapshot` + `OrderTimeline` + `OrderActions` + `CancelOrderModal`
- [x] 11.5 Pasar `adminMode` a `OrderActions` para determinar qué acciones renderizar
- [x] 11.6 Envolver la página con `React.lazy` en el router para code splitting

## 12. Registro de rutas en el router

- [x] 12.1 Localizar el archivo de routing (probablemente `frontend/src/app/router.tsx` o `frontend/src/shared/routing/`) y añadir ruta lazy `/pedidos/:id` con `ProtectedRoute` restringido a rol CLIENT
- [x] 12.2 Añadir ruta lazy `/admin/pedidos/:id` con `ProtectedRoute` restringido a roles ADMIN y PEDIDOS, con `adminMode={true}` en `OrderDetailPage`
- [x] 12.3 Verificar que ambas rutas usan `React.lazy(() => import('@/pages/OrderDetailPage'))` y están envueltas en `Suspense`

## 13. Actualizar OrderCard para navegar al detalle

- [x] 13.1 Añadir a `OrderCard.tsx` existente un botón/enlace "Ver detalle" que navega a `/pedidos/:id` para modo CLIENT o a `/admin/pedidos/:id` para modo admin
- [x] 13.2 Usar `<Link>` de react-router-dom (no `<a>`) para aprovechar el router client-side
- [x] 13.3 Añadir `aria-label={`Ver detalle del pedido #${order.id}`}` al enlace

## 14. Tests Vitest (unitarios / integración)

- [x] 14.1 Crear `frontend/src/features/orders/components/detail/__tests__/OrderItemSnapshot.test.tsx` — verificar que renderiza `nombre_snapshot` y `precio_snapshot`, NO el nombre o precio actual del producto; verificar que personalización vacía no renderiza sección
- [x] 14.2 Crear `frontend/src/features/orders/components/detail/__tests__/OrderTimeline.test.tsx` — verificar que renderiza N ítems para N entradas de historial; verificar orden cronológico; verificar fallback "Sistema" cuando `usuario_email` es null
- [x] 14.3 Crear `frontend/src/features/orders/components/detail/__tests__/CancelOrderModal.test.tsx` — verificar que el modal tiene `role="dialog"`; verificar que Escape cierra sin ejecutar la mutation; verificar que botón "Sí, cancelar" llama a la mutation
- [x] 14.4 Crear `frontend/src/features/orders/components/detail/__tests__/OrderActions.test.tsx` — verificar que botón "Cancelar" es disabled con `aria-disabled="true"` cuando `estado_pedido_id !== 1`; verificar que estados terminales muestran mensaje sin botones
- [x] 14.5 Correr `npx vitest run` desde `frontend/` y confirmar que todos los tests pasan (cobertura ≥ 40% del feature)

## 15. Tests E2E Playwright

- [x] 15.1 Crear `frontend/e2e/orders/order-detail.spec.ts` con el helper `loginAs` de `e2e/helpers/auth.ts`
- [x] 15.2 Test: CLIENT ve detalle de su pedido — seedear auth como CLIENT, mockear `GET /api/v1/pedidos/1` con objeto `OrderDetail` válido, navegar a `/pedidos/1`, verificar que el ID del pedido y la timeline son visibles
- [x] 15.3 Test: Timeline con múltiples estados — mock con `historial` de 3 ítems, verificar que 3 ítems de timeline son visibles en el DOM
- [x] 15.4 Test: CLIENT cancela pedido PENDIENTE con confirmación — mock con `estado_pedido_id=1`, mockear `DELETE /api/v1/pedidos/1` con 200, hacer click en "Cancelar pedido", esperar modal, hacer click en "Sí, cancelar", verificar toast de éxito
- [x] 15.5 Test: Modal se cierra con Escape sin ejecutar request — verificar que `DELETE /api/v1/pedidos/1` no fue llamado
- [x] 15.6 Test: CLIENT sin auth → redirige a `/login`
- [x] 15.7 Test: CLIENT intenta `/admin/pedidos/1` → redirige a `/403`
- [x] 15.8 Test: Pedido no encontrado (404) → muestra estado de error con CTA "Volver a mis pedidos"
- [x] 15.9 Correr `npx playwright test e2e/orders/order-detail.spec.ts` y confirmar que todos los scenarios pasan

## 16. Verificación final pre-archive

- [x] 16.1 Leer `.agents/skills/post-change-verification/SKILL.md` y ejecutar el health check completo
- [x] 16.2 Correr `npx vitest run` desde `frontend/` — todos los tests en verde
- [x] 16.3 Correr `npm run lint` desde `frontend/` — sin errores
- [x] 16.4 Correr `npx tsc --noEmit` desde `frontend/` — sin errores de tipos
- [x] 16.5 Verificar que NINGÚN componente nuevo usa `useEffect + fetch` (todo server state pasa por TanStack Query)
- [x] 16.6 Verificar que el store `useOrderDetailStore` NO almacena datos del pedido (solo `isCancelModalOpen`)
- [x] 16.7 Verificar que todos los imports usan path alias `@/` (sin imports relativos que crucen features)
- [x] 16.8 Verificar que ningún componente nuevo usa colores hardcodeados (solo tokens semánticos `@theme`)
- [x] 16.9 Correr `npm run dev` y probar manualmente: navegar a `/pedidos/:id` como CLIENT, ver detalle, cancelar, verificar toast
