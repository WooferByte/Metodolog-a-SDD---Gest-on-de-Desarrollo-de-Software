## ADDED Requirements

### Requirement: ProtectedRoute redirects unauthenticated users to login
The system SHALL redirect any unauthenticated user who navigates to a protected route to the `/login` page, preserving the original destination in `location.state.from` for post-login redirect.

#### Scenario: Unauthenticated user accesses protected route
- **WHEN** a user with `isAuthenticated = false` and `_hasHydrated = true` navigates to a protected route
- **THEN** the system SHALL render `<Navigate to="/login" state={{ from: location }} replace />`

#### Scenario: Login page receives redirect state
- **WHEN** unauthenticated user is redirected to `/login`
- **THEN** `location.state.from` SHALL contain the originally requested path

### Requirement: ProtectedRoute blocks users without required roles
The system SHALL redirect authenticated users who lack the required role(s) to the `/403` page.

#### Scenario: Authenticated user missing required role
- **WHEN** a user with `isAuthenticated = true` and `_hasHydrated = true` navigates to a route with `requiredRoles={['ADMIN']}` and the user's roles do not include `ADMIN`
- **THEN** the system SHALL render `<Navigate to="/403" replace />`

#### Scenario: Authenticated user has at least one required role
- **WHEN** a user with `isAuthenticated = true` navigates to a route with `requiredRoles={['CLIENT', 'ADMIN']}` and the user has role `ADMIN`
- **THEN** the system SHALL render `<Outlet />` (allowing access)

### Requirement: ProtectedRoute defers rendering until store is hydrated
The system SHALL NOT redirect before the Zustand auth store has rehydrated from localStorage.

#### Scenario: Store not yet hydrated on page reload
- **WHEN** `_hasHydrated = false` regardless of `isAuthenticated` value
- **THEN** the system SHALL render a loading indicator and SHALL NOT render a `<Navigate>` redirect

#### Scenario: Store hydrated and authenticated
- **WHEN** `_hasHydrated = true` and `isAuthenticated = true` and no `requiredRoles` are defined
- **THEN** the system SHALL render `<Outlet />`

### Requirement: ProtectedRoute composes with react-router-dom v6 nested routes
The system SHALL use `<Outlet />` as its pass-through render, enabling it to act as a layout route wrapper for groups of child routes.

#### Scenario: Route group wrapping
- **WHEN** multiple routes are nested under a single `<ProtectedRoute>` via react-router-dom's layout route pattern
- **THEN** all child routes SHALL inherit the authentication and role checks of the parent `<ProtectedRoute>`

### Requirement: Route configuration assigns correct requiredRoles per route group
The application router SHALL apply the following access control mapping:

| Route(s) | requiredRoles |
|----------|--------------|
| `/`, `/catalog`, `/login`, `/register` | (public — no ProtectedRoute) |
| `/cart`, `/orders`, `/profile`, `/addresses` | `['CLIENT', 'ADMIN']` |
| `/admin/productos`, `/admin/categorias`, `/admin/ingredientes` | `['STOCK', 'ADMIN']` |
| `/admin/pedidos` | `['PEDIDOS', 'ADMIN']` |
| `/admin/usuarios`, `/admin/metricas`, `/admin/configuracion` | `['ADMIN']` |

#### Scenario: CLIENT user accesses orders
- **WHEN** a user with role `CLIENT` navigates to `/orders`
- **THEN** the system SHALL render the Orders page (role check passes)

#### Scenario: STOCK user blocked from admin users page
- **WHEN** a user with role `STOCK` navigates to `/admin/usuarios`
- **THEN** the system SHALL redirect to `/403`
