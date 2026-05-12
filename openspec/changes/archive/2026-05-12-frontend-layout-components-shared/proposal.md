## Why

The frontend currently has a minimal `Navbar` and a `ToastContainer` but lacks a proper layout shell (sidebar, main content area, footer), atomic UI primitives (Button, Input, Card, Modal, Badge, Skeleton), and a unified Tailwind v4 design-token layer. As a result, every future feature change would need to define its own styling conventions and lay out its own page skeleton from scratch, creating inconsistency and duplicated effort. This change establishes the shared visual foundation that all subsequent frontend changes (catalog, cart, checkout, admin) will build on.

## What Changes

- Add `AppLayout` wrapper component (`shared/components/layout/`) — top Navbar + optional collapsible Sidebar + `<main>` content slot + Footer
- Extend existing `Navbar.tsx` — add hamburger toggle that drives `uiStore.toggleSidebar`, responsive mobile menu, theme-toggle button
- Add `Sidebar.tsx` — role-aware vertical nav driven by `uiStore.sidebarOpen`; uses `useNavLinks` pattern already in the codebase
- Add `Footer.tsx` — minimal branding/copyright strip
- Add atomic components in `shared/components/ui/`:
  - `Button` — variants (primary, secondary, outline, ghost, destructive) + sizes + loading state
  - `Input` — with label, error message, optional icon slots
  - `Card` / `CardHeader` / `CardContent` / `CardFooter` — compound pattern
  - `Modal` — focus-trapped dialog (accessible, keyboard-dismissible)
  - `Badge` — color variants (default, success, warning, error, info)
  - `Skeleton` — animated loading placeholder in multiple shapes
- Add `cn()` utility (`shared/lib/utils.ts`) — `clsx` + `tailwind-merge`
- Add Tailwind v4 `@theme` design-token block in `index.css` — semantic color tokens (OKLCH), radius tokens, animation tokens, dark-mode variant
- Wire dark-mode toggle: `uiStore.theme` drives `.dark` class on `<html>`
- Update `App.tsx` to use `AppLayout`
- Write vitest unit tests for all new components

## Capabilities

### New Capabilities

- `shared-layout`: `AppLayout`, `Navbar` (extended), `Sidebar`, `Footer` — the page-level shell that wraps every route
- `shared-ui-primitives`: `Button`, `Input`, `Card`, `Modal`, `Badge`, `Skeleton` — atomic building blocks reused across all feature pages
- `design-tokens`: Tailwind v4 `@theme` block — semantic OKLCH color tokens, spacing/radius/animation tokens, dark-mode CSS variant

### Modified Capabilities

- `shared-components`: Existing `Navbar.tsx` gains sidebar toggle, mobile hamburger, and theme-toggle — this is a behavioral extension, not a breaking replacement

## Impact

- **Files modified**: `frontend/src/app/App.tsx`, `frontend/src/shared/components/Navbar.tsx`, `frontend/src/index.css`
- **Files added**: `shared/components/layout/AppLayout.tsx`, `Sidebar.tsx`, `Footer.tsx`; `shared/components/ui/Button.tsx`, `Input.tsx`, `Card.tsx`, `Modal.tsx`, `Badge.tsx`, `Skeleton.tsx`; `shared/lib/utils.ts`; tests for all new components
- **Dependencies**: No new npm packages required (`lucide-react`, `tailwind` v4 already installed). `clsx` and `tailwind-merge` need to be installed.
- **Breaking changes**: None — existing pages continue to work; `App.tsx` refactor is additive
- **FSD layer**: Everything lives in `shared/` — safely imported by Pages, Widgets, Features, and Entities
