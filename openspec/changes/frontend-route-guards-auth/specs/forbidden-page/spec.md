## ADDED Requirements

### Requirement: ForbiddenPage displays a clear 403 access denied message
The system SHALL render a dedicated 403 Forbidden page when a user navigates to `/403` or is redirected there by `ProtectedRoute`.

#### Scenario: User reaches the 403 page
- **WHEN** a user navigates to `/403`
- **THEN** the system SHALL display a heading indicating access is denied and a descriptive message explaining the user lacks permissions for the requested page

#### Scenario: Page is styled with Tailwind v4
- **WHEN** the ForbiddenPage is rendered
- **THEN** it SHALL use only Tailwind v4 utility classes and SHALL NOT use inline `style={{}}` props

### Requirement: ForbiddenPage provides navigation back to home
The system SHALL include a button or link that navigates the user back to the home page (`/`) from the 403 page.

#### Scenario: User clicks "Volver al inicio"
- **WHEN** a user on the `/403` page clicks the "Volver al inicio" button
- **THEN** the system SHALL navigate the user to `/`

### Requirement: ForbiddenPage is accessible
The ForbiddenPage SHALL meet WCAG 2.1 Level AA accessibility requirements.

#### Scenario: Screen reader accessibility
- **WHEN** a screen reader navigates the ForbiddenPage
- **THEN** the heading SHALL use a semantic `<h1>` element and the page SHALL have meaningful text content

#### Scenario: Keyboard navigation
- **WHEN** a keyboard user presses Tab on the ForbiddenPage
- **THEN** the "Volver al inicio" button SHALL be focusable and SHALL have a visible focus ring
