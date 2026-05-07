## ADDED Requirements

### Requirement: UIStore manages application theme

The uiStore SHALL maintain current theme preference (light or dark mode) with localStorage persistence.

#### Scenario: Initial theme state
- **WHEN** application first loads
- **THEN** theme defaults to 'light' or restored from localStorage

#### Scenario: Set theme
- **WHEN** user toggles dark mode
- **THEN** uiStore.setTheme('dark') updates state and persists to localStorage

#### Scenario: Get current theme
- **WHEN** component queries uiStore for theme
- **THEN** returns 'light' or 'dark' string

#### Scenario: Persist theme preference
- **WHEN** user changes theme and closes browser
- **THEN** theme setting is restored on next visit

### Requirement: UIStore manages sidebar navigation state

The uiStore SHALL track whether sidebar is open or closed for responsive mobile navigation.

#### Scenario: Initial sidebar state
- **WHEN** application loads
- **THEN** sidebarOpen defaults to true (or based on screen size)

#### Scenario: Toggle sidebar
- **WHEN** user clicks hamburger menu
- **THEN** uiStore.toggleSidebar() flips sidebarOpen state

#### Scenario: Get sidebar state
- **WHEN** Layout component queries sidebar state
- **THEN** returns boolean indicating if sidebar is open

### Requirement: UIStore manages toast notifications

The uiStore SHALL maintain array of active toast notifications for user feedback (errors, success, info).

#### Scenario: Add toast notification
- **WHEN** API error occurs
- **THEN** uiStore.addToast({ type: 'error', message: '...' }) adds to toasts array

#### Scenario: Remove toast after timeout
- **WHEN** toast is displayed for 3 seconds
- **THEN** uiStore.removeToast(toastId) removes it from array

#### Scenario: Retrieve active toasts
- **WHEN** Toast container component renders
- **THEN** queries uiStore.getToasts() to display all active notifications

### Requirement: UIStore persists only theme to localStorage

The uiStore SHALL selectively persist only the theme preference, not sidebar or toasts.

#### Scenario: Theme persisted, sidebar not
- **WHEN** user changes theme and sidebar
- **THEN** localStorage contains theme but NOT sidebar state

#### Scenario: Sidebar resets on reload
- **WHEN** page reloads
- **THEN** sidebar state resets to default, theme is restored

#### Scenario: Toasts cleared on reload
- **WHEN** page reloads
- **THEN** toasts array is empty (no persistence)

