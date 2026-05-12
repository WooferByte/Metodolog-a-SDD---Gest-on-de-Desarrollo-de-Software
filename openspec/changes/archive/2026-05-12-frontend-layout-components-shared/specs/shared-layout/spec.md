## ADDED Requirements

### Requirement: AppLayout wraps all routes
The system SHALL provide an `AppLayout` component in `shared/components/layout/AppLayout.tsx` that renders the global `Navbar`, an optional `Sidebar`, a `<main>` content area for page routes, and a `Footer`. All routes SHALL be rendered as children of `AppLayout`.

#### Scenario: Layout renders children in main content area
- **WHEN** a route renders inside `AppLayout`
- **THEN** the route content appears inside a `<main>` element with id `main-content`

#### Scenario: Sidebar is hidden when sidebarOpen is false
- **WHEN** `uiStore.sidebarOpen` is `false`
- **THEN** the `Sidebar` component is not visible (hidden or unmounted)

#### Scenario: Sidebar is visible when sidebarOpen is true
- **WHEN** `uiStore.sidebarOpen` is `true`
- **THEN** the `Sidebar` component is visible

### Requirement: Sidebar is role-aware and driven by uiStore
The system SHALL provide a `Sidebar` component in `shared/components/layout/Sidebar.tsx` that uses `useNavLinks()` to render role-appropriate navigation links. The Sidebar SHALL be toggled by `uiStore.toggleSidebar`.

#### Scenario: Authenticated ADMIN user sees all nav links in Sidebar
- **WHEN** user has role `ADMIN` and `sidebarOpen` is `true`
- **THEN** the Sidebar renders all admin navigation links

#### Scenario: Unauthenticated user sees no Sidebar links requiring auth
- **WHEN** user is not authenticated and `sidebarOpen` is `true`
- **THEN** the Sidebar renders only public navigation links

#### Scenario: Sidebar closes on Escape key (mobile)
- **WHEN** user presses `Escape` and viewport is below `1024px`
- **THEN** `uiStore.toggleSidebar` is called to close the Sidebar

### Requirement: Footer renders at the bottom of every page
The system SHALL provide a `Footer` component in `shared/components/layout/Footer.tsx` with a copyright notice.

#### Scenario: Footer is always visible
- **WHEN** any route renders inside `AppLayout`
- **THEN** a `<footer>` element with copyright text is present in the DOM

### Requirement: Layout is responsive — mobile-first
The `AppLayout` SHALL use a mobile-first approach: on viewports below `1024px`, the Sidebar overlays with a semi-transparent backdrop; on `1024px` and above, the Sidebar is a persistent left panel that shifts the `<main>` content right.

#### Scenario: Mobile layout — Sidebar overlays
- **WHEN** viewport is below 1024px and Sidebar is open
- **THEN** a backdrop overlay covers the main content behind the Sidebar

#### Scenario: Desktop layout — Sidebar is persistent panel
- **WHEN** viewport is 1024px or wider and Sidebar is open
- **THEN** the main content area is shifted right by the Sidebar width with no backdrop
