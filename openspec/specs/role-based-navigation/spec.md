# role-based-navigation Specification

## Purpose
TBD - created by archiving change frontend-navigation-by-role. Update Purpose after archive.
## Requirements
### Requirement: Navbar renders role-specific navigation links
The system SHALL render a different set of navigation links in `Navbar.tsx` depending on the authenticated user's role. Link sets are computed by `useNavLinks` hook from `authStore` state.

#### Scenario: Unauthenticated user sees public links only
- **WHEN** `isAuthenticated` is false
- **THEN** the navbar shows: Catálogo (`/catalog`), Iniciar sesión (`/login`), Registrarse (`/register`)
- **AND** no authenticated-only links are visible

#### Scenario: CLIENT user sees client links
- **WHEN** the user has role `CLIENT`
- **THEN** the navbar shows: Catálogo, Carrito (`/cart`), Mis Pedidos (`/orders`), Mi Perfil (`/profile`), Mis Direcciones (`/addresses`)
- **AND** no admin or stock links are visible

#### Scenario: STOCK user sees stock management links
- **WHEN** the user has role `STOCK`
- **THEN** the navbar shows: Productos (`/admin/productos`), Categorías (`/admin/categorias`), Ingredientes (`/admin/ingredientes`)

#### Scenario: PEDIDOS user sees order management link
- **WHEN** the user has role `PEDIDOS`
- **THEN** the navbar shows: Panel Pedidos (`/admin/pedidos`)

#### Scenario: ADMIN user sees full navigation
- **WHEN** the user has role `ADMIN`
- **THEN** the navbar shows: Catálogo, Mis Pedidos, Usuarios (`/admin/usuarios`), Pedidos (`/admin/pedidos`), Métricas (`/admin/metricas`), Configuración (`/admin/configuracion`)

### Requirement: Navbar always shows logout for authenticated users
The system SHALL render a logout button for any authenticated user regardless of role.

#### Scenario: Authenticated user sees logout button
- **WHEN** `isAuthenticated` is true
- **THEN** a logout button is visible and functional
- **AND** clicking it calls the `logout` action from `useLogout` hook

#### Scenario: Unauthenticated user does not see logout button
- **WHEN** `isAuthenticated` is false
- **THEN** no logout button is rendered

### Requirement: useNavLinks hook is independently testable
The system SHALL expose a `useNavLinks(): NavLink[]` hook at `shared/hooks/useNavLinks.ts` that returns the array of `{ label: string; to: string }` objects for the current auth state.

#### Scenario: Hook returns unauthenticated links when user is null
- **WHEN** `useNavLinks` is called with `user === null`
- **THEN** it returns exactly the 3 public links

#### Scenario: Hook returns CLIENT links when user has CLIENT role
- **WHEN** `useNavLinks` is called with a user whose roles include `CLIENT`
- **THEN** it returns the 5 client links

#### Scenario: Hook returns ADMIN links when user has ADMIN role
- **WHEN** `useNavLinks` is called with a user whose roles include `ADMIN`
- **THEN** it returns the 6 admin links

### Requirement: Navbar uses Tailwind v4 utility classes exclusively
The system SHALL style `Navbar.tsx` using Tailwind v4 utility classes only. No inline `style={{}}` props are allowed in the new implementation.

#### Scenario: Navbar renders without inline styles
- **WHEN** the Navbar component is inspected
- **THEN** no `style` prop exists on any element in the component tree

