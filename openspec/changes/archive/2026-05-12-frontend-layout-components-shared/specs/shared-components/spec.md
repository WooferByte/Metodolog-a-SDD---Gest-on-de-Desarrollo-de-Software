## MODIFIED Requirements

### Requirement: Navbar includes sidebar toggle and theme toggle
The existing `Navbar` component in `shared/components/Navbar.tsx` SHALL be extended to include: (1) a hamburger button on the left that calls `uiStore.toggleSidebar`, with `aria-label="Abrir menú"` / `aria-label="Cerrar menú"` toggled based on `sidebarOpen` state; (2) a theme-toggle button on the right that calls `uiStore.setTheme` to switch between `light` and `dark`. All existing role-aware nav link and auth/logout logic SHALL remain unchanged.

#### Scenario: Hamburger button toggles sidebar
- **WHEN** user clicks the hamburger button in the Navbar
- **THEN** `uiStore.toggleSidebar()` is called and `sidebarOpen` state changes

#### Scenario: Hamburger aria-label reflects sidebar state
- **WHEN** `sidebarOpen` is `false`
- **THEN** hamburger button has `aria-label="Abrir menú"`
- **WHEN** `sidebarOpen` is `true`
- **THEN** hamburger button has `aria-label="Cerrar menú"`

#### Scenario: Theme toggle switches between light and dark
- **WHEN** user clicks the theme-toggle button while theme is `light`
- **THEN** `uiStore.setTheme('dark')` is called

#### Scenario: Existing nav links still render correctly after modification
- **WHEN** Navbar renders with an authenticated CLIENT user
- **THEN** the same nav links as before appear (no regression)
