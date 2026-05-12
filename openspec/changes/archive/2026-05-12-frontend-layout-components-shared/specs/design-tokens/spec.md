## ADDED Requirements

### Requirement: Tailwind v4 @theme semantic color tokens
The system SHALL define all semantic color tokens in the `@theme {}` block inside `frontend/src/index.css` using OKLCH color values. Tokens SHALL include: `--color-background`, `--color-foreground`, `--color-primary`, `--color-primary-foreground`, `--color-secondary`, `--color-secondary-foreground`, `--color-muted`, `--color-muted-foreground`, `--color-accent`, `--color-accent-foreground`, `--color-destructive`, `--color-destructive-foreground`, `--color-border`, `--color-ring`, `--color-card`, `--color-card-foreground`.

#### Scenario: Semantic color utilities are available in components
- **WHEN** a component uses `bg-primary` Tailwind class
- **THEN** the CSS custom property `--color-primary` value is applied as background

#### Scenario: All color tokens use OKLCH color space
- **WHEN** the @theme block is parsed
- **THEN** all `--color-*` values use `oklch(...)` format

### Requirement: Tailwind v4 @theme radius and animation tokens
The system SHALL define radius tokens (`--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`) and animation tokens (`--animate-fade-in`, `--animate-fade-out`, `--animate-slide-in`) in the `@theme {}` block with corresponding `@keyframes` definitions.

#### Scenario: Radius tokens are usable as Tailwind utilities
- **WHEN** a component uses `rounded-md` class
- **THEN** the `--radius-md` token value is applied as border-radius

#### Scenario: Animation tokens produce CSS animations
- **WHEN** `animate-fade-in` class is applied to an element
- **THEN** the element animates with the `fade-in` keyframe

### Requirement: Dark mode CSS variant and overrides
The system SHALL define `@custom-variant dark (&:where(.dark, .dark *))` and a `.dark {}` block in `index.css` that overrides all semantic color tokens with dark-mode OKLCH values. The `.dark` class applied to `<html>` SHALL activate all dark-mode overrides.

#### Scenario: Dark mode activates when .dark class is on html
- **WHEN** `document.documentElement.classList.add('dark')` is called
- **THEN** all `--color-*` tokens switch to their dark-mode OKLCH values

#### Scenario: Dark mode overrides maintain WCAG AA contrast
- **WHEN** dark mode is active
- **THEN** `--color-foreground` on `--color-background` maintains at least 4.5:1 contrast ratio

### Requirement: Theme synchronization from uiStore to DOM
The system SHALL apply the `.dark` class to `document.documentElement` whenever `uiStore.theme === 'dark'`, and remove it when `uiStore.theme === 'light'`. This SHALL be done in `App.tsx` via a `useEffect` subscribing to `useUIStore`.

#### Scenario: Setting theme to dark applies .dark class to html
- **WHEN** `uiStore.setTheme('dark')` is called
- **THEN** `document.documentElement.classList.contains('dark')` is `true`

#### Scenario: Setting theme to light removes .dark class from html
- **WHEN** `uiStore.setTheme('light')` is called
- **THEN** `document.documentElement.classList.contains('dark')` is `false`
