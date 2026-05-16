## ADDED Requirements

### Requirement: CLIENT puede ver su historial de pedidos en /mis-pedidos
El sistema SHALL renderizar en `/mis-pedidos` una lista paginada de pedidos del usuario autenticado con rol CLIENT. Los pedidos se muestran en formato timeline visual (tarjetas OrderCard), ordenados por fecha descendente. Solo los usuarios con rol CLIENT pueden acceder a esta ruta; cualquier otro rol DEBE ser redirigido.

#### Scenario: CLIENT con pedidos accede a /mis-pedidos
- **WHEN** un usuario autenticado con rol CLIENT navega a `/mis-pedidos`
- **THEN** el sistema muestra una lista de OrderCard con estado badge, fecha formateada, total en pesos argentinos y CTA al detalle de cada pedido

#### Scenario: CLIENT sin pedidos accede a /mis-pedidos
- **WHEN** un usuario autenticado con rol CLIENT navega a `/mis-pedidos` y no tiene pedidos registrados
- **THEN** el sistema muestra un estado vacío con mensaje "No tenés pedidos todavía" y un CTA al catálogo de productos

#### Scenario: Página cargando — skeleton visible
- **WHEN** la petición a `GET /api/v1/pedidos` está en vuelo
- **THEN** el sistema muestra skeletons con la forma aproximada de las OrderCard en lugar de spinners genéricos

#### Scenario: Usuario no autenticado accede a /mis-pedidos
- **WHEN** un usuario no autenticado navega a `/mis-pedidos`
- **THEN** el sistema redirige a `/login`

#### Scenario: Paginación avanza sin flash
- **WHEN** el usuario navega a la siguiente página de pedidos
- **THEN** los datos anteriores permanecen visibles hasta que la nueva página responde (`keepPreviousData`), sin mostrar un estado de carga en blanco

---

### Requirement: ADMIN y PEDIDOS pueden gestionar pedidos en /admin/pedidos
El sistema SHALL renderizar en `/admin/pedidos` una tabla paginada con todos los pedidos del sistema, accesible únicamente para usuarios con rol ADMIN o PEDIDOS. La tabla DEBE incluir columnas de usuario (email), fecha, total, estado (badge) y acciones (ver detalle). Roles sin acceso (CLIENT, STOCK) DEBEN ser redirigidos a `/403`.

#### Scenario: ADMIN accede a /admin/pedidos y ve tabla con pedidos
- **WHEN** un usuario con rol ADMIN navega a `/admin/pedidos`
- **THEN** el sistema muestra una tabla con filas que contienen: email del usuario, fecha formateada, total, badge de estado y botón "Ver detalle"

#### Scenario: PEDIDOS accede a /admin/pedidos
- **WHEN** un usuario con rol PEDIDOS navega a `/admin/pedidos`
- **THEN** el sistema muestra la misma tabla completa que para ADMIN

#### Scenario: CLIENT intenta acceder a /admin/pedidos
- **WHEN** un usuario con rol CLIENT navega a `/admin/pedidos`
- **THEN** el sistema redirige a `/403`

#### Scenario: Skeleton de tabla mientras carga
- **WHEN** la petición a `GET /api/v1/pedidos` está en vuelo en la vista admin
- **THEN** el sistema muestra filas de skeleton en la tabla en lugar de una tabla vacía

#### Scenario: Sin pedidos en el sistema
- **WHEN** el backend responde con `{ items: [], total: 0 }`
- **THEN** la tabla muestra una fila de estado vacío con mensaje "No hay pedidos registrados"

---

### Requirement: Filtros de tabla en panel admin gestionados con Zustand
El sistema SHALL proveer en `/admin/pedidos` filtros por estado de pedido, rango de fecha y búsqueda por email de usuario. Los filtros DEBEN estar gestionados con Zustand v5 (estado cliente) y DEBEN usarse como query params al invocar `GET /api/v1/pedidos`. Los filtros NO DEBEN duplicar los datos del servidor en el store.

#### Scenario: Filtrar por estado PENDIENTE
- **WHEN** el ADMIN selecciona "PENDIENTE" en el selector de estado
- **THEN** la tabla se actualiza mostrando únicamente pedidos con estado PENDIENTE, y el query a la API incluye el parámetro de filtro correspondiente

#### Scenario: Limpiar filtros restaura la lista completa
- **WHEN** el ADMIN hace click en "Limpiar filtros"
- **THEN** todos los filtros del store Zustand se resetean y la tabla muestra todos los pedidos sin filtro

#### Scenario: Filtros persisten al cambiar de página
- **WHEN** el ADMIN aplica un filtro y luego cambia de página con la paginación
- **THEN** el filtro sigue activo y la nueva página respeta el filtro aplicado

---

### Requirement: OrderStatusBadge renderiza estado semántico por ID
El sistema SHALL mapear los IDs de estado numéricos (1–6) a badges con colores semánticos usando tokens `@theme` de Tailwind v4. Los colores DEBEN ser exclusivamente tokens semánticos; está PROHIBIDO usar valores de color hardcodeados.

#### Scenario: Estado PENDIENTE muestra badge amarillo
- **WHEN** se renderiza `OrderStatusBadge` con `statusId=1`
- **THEN** el badge muestra el texto "PENDIENTE" con el token de color `--color-warning` (amarillo)

#### Scenario: Estado ENTREGADO muestra badge verde
- **WHEN** se renderiza `OrderStatusBadge` con `statusId=5`
- **THEN** el badge muestra el texto "ENTREGADO" con el token de color `--color-success` (verde)

#### Scenario: Estado CANCELADO muestra badge gris
- **WHEN** se renderiza `OrderStatusBadge` con `statusId=6`
- **THEN** el badge muestra el texto "CANCELADO" con el token de color `--color-muted-foreground` (gris)

#### Scenario: ID de estado desconocido
- **WHEN** se renderiza `OrderStatusBadge` con un `statusId` que no existe en el mapa
- **THEN** el badge muestra el texto "DESCONOCIDO" con el token de color muted, sin error de runtime

---

### Requirement: OrderCard es accesible y responsive
El componente `OrderCard` SHALL ser accesible (WCAG 2.1 AA) y responsive mobile-first. En modo `"client"` se presenta como tarjeta timeline. En modo `"admin"` se presenta como fila de tabla compacta. El componente DEBE funcionar en ambos modos sin romper el layout.

#### Scenario: OrderCard en modo client — estructura correcta
- **WHEN** se renderiza `<OrderCard mode="client" order={...} />`
- **THEN** el componente muestra badge de estado, fecha, total y un enlace/botón "Ver detalle" accesible con `aria-label` descriptivo

#### Scenario: OrderCard en modo admin — estructura compacta
- **WHEN** se renderiza `<OrderCard mode="admin" order={...} />`
- **THEN** el componente muestra los datos en formato compacto adecuado para fila de tabla

#### Scenario: Responsive mobile
- **WHEN** se renderiza `MyOrdersPage` en viewport mobile (< 640px)
- **THEN** las OrderCard se muestran en una sola columna con padding adecuado y texto legible sin overflow

---

### Requirement: Cobertura de tests vitest mínima para componentes de orders
El sistema SHALL incluir tests vitest en `__tests__/` para los componentes `OrderCard` (modo client y admin), `OrdersSkeleton` y el estado vacío. La cobertura DEBE alcanzar al menos 40% de las líneas del feature `orders`.

#### Scenario: Test renderiza OrderCard modo client
- **WHEN** se ejecuta `vitest run` y el test de `OrderCard` con `mode="client"`
- **THEN** el test verifica que el badge de estado, la fecha y el total estén presentes en el DOM

#### Scenario: Test renderiza skeleton
- **WHEN** se ejecuta `vitest run` y el test de `OrdersSkeleton`
- **THEN** el test verifica que N elementos de skeleton están presentes (uno por tarjeta esperada)

#### Scenario: Test estado vacío
- **WHEN** se ejecuta `vitest run` y el test de estado vacío de `MyOrdersPage`
- **THEN** el test verifica que el mensaje "No tenés pedidos todavía" está presente cuando `items=[]`

---

### Requirement: Tests E2E Playwright cubren flujos de listado por rol
El sistema SHALL incluir un archivo `frontend/src/e2e/orders-listing.spec.ts` que cubra: listar pedidos como CLIENT, listar como ADMIN/PEDIDOS, filtrar por estado, paginar y verificar redirect de acceso no autorizado.

#### Scenario: E2E — CLIENT ve sus pedidos
- **WHEN** el test de Playwright usa `loginAs(page, 'CLIENT')` y navega a `/mis-pedidos`
- **THEN** el test verifica que hay al menos una OrderCard visible o el estado vacío

#### Scenario: E2E — ADMIN ve tabla de pedidos
- **WHEN** el test de Playwright usa `loginAs(page, 'ADMIN')` y navega a `/admin/pedidos`
- **THEN** el test verifica que la tabla con `role="table"` es visible

#### Scenario: E2E — CLIENT no puede acceder a /admin/pedidos
- **WHEN** el test de Playwright usa `loginAs(page, 'CLIENT')` y navega a `/admin/pedidos`
- **THEN** la URL resulta en `/403`

#### Scenario: E2E — filtro por estado funciona
- **WHEN** el test de Playwright selecciona un estado en el filtro y espera la respuesta mockeada
- **THEN** la tabla actualiza su contenido mostrando solo los pedidos del estado seleccionado
