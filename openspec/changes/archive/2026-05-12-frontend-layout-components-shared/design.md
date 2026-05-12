## Context

The Food Store frontend uses React 18, TypeScript strict, Tailwind v4 (CSS-first, no `tailwind.config.ts`), Zustand v5 for client state, and FSD (`Pages → Widgets → Features → Entities → Shared`). Two shared components already exist: `Navbar.tsx` (role-aware, uses `useNavLinks` hook and `useAuthStore`) and `ToastContainer.tsx` (consumes `uiStore.toasts`). The `uiStore` already exposes `sidebarOpen`, `toggleSidebar`, and `theme`/`setTheme`. Icons come from `lucide-react`. No `cn()` utility or design-token layer exists yet.

All future feature changes (catalog, cart, admin CRUD) will build UI on top of the primitives introduced here. Getting this layer right — token names, component API surface, accessibility — is high-leverage because it cannot easily be refactored later without touching many files.

## Goals / Non-Goals

**Goals:**
- Establish a single `AppLayout` shell (Navbar + optional Sidebar + main + Footer) wrapping every route
- Extend `Navbar` with sidebar hamburger toggle and dark-mode theme toggle, without breaking existing role/auth logic
- Provide a `Sidebar` component driven by `uiStore.sidebarOpen` and reusing `useNavLinks` for role-aware links
- Ship six atomic primitives (Button, Input, Card, Modal, Badge, Skeleton) with full TypeScript prop types and WCAG AA accessibility
- Define all color/radius/animation design tokens once in `index.css` using Tailwind v4 `@theme` — all components use semantic class names (`bg-primary`, `text-muted-foreground`, etc.)
- Wire dark mode: `uiStore.theme` drives the `.dark` class on `<html>`, making all `@theme`-based dark overrides activate automatically
- Add `cn()` utility (`clsx` + `tailwind-merge`) used by all new components
- Write vitest unit tests (≥40% coverage threshold) for all new components

**Non-Goals:**
- Radix UI or shadcn/ui installation — primitives are hand-built with Tailwind v4; Radix can be added later
- `@tanstack/react-form` integration — deferred to the formularios change
- Animation library — CSS-native `@keyframes` in `@theme` only
- Storybook — out of scope for this change
- Mobile drawer behavior for Sidebar — overlay-style slide-in is sufficient; full drawer primitive is deferred

## Decisions

### D1: `cn()` via `clsx` + `tailwind-merge` — install two packages

**Decision**: Add `clsx` and `tailwind-merge` as runtime dependencies. Create `frontend/src/shared/lib/utils.ts` exporting `cn()`.

**Rationale**: These are the de-facto standard for Tailwind component libraries. `tailwind-merge` resolves conflicting utility classes (e.g., caller passing `bg-red-500` to a component that has `bg-primary`). Alternatives considered:
- `cva` (Class Variance Authority): powerful for variants but adds another dependency; we'll use plain CVA-style objects without the library to keep the bundle lean.
- Manual string concatenation: fragile and doesn't deduplicate conflicting utilities.

### D2: Design tokens in `index.css` `@theme` block — CSS-first, no config file

**Decision**: Define all semantic tokens (`--color-primary`, `--color-muted-foreground`, `--radius-md`, etc.) in `@theme {}` inside `frontend/src/index.css`. Dark-mode overrides go in a `.dark {}` block using `@custom-variant dark (&:where(.dark, .dark *))`.

**Rationale**: Tailwind v4 is CSS-first — `tailwind.config.ts` is deprecated. Tokens defined in `@theme` become Tailwind utility classes automatically (e.g., `bg-primary`, `text-muted-foreground`). This is the canonical v4 pattern from the `tailwind-design-system` skill. Using OKLCH for color values provides perceptual uniformity and better dark-mode calculations.

### D3: Dark-mode driven by `uiStore.theme` — class on `<html>`

**Decision**: In `App.tsx` (or a dedicated `ThemeApplier` effect), subscribe to `uiStore.theme` and toggle the `dark` class on `document.documentElement`. The `@custom-variant dark` in CSS activates on `.dark` parent.

**Rationale**: `uiStore` already persists `theme` to localStorage. A single `useEffect` in App.tsx is the minimal approach. Alternatives considered:
- CSS `prefers-color-scheme` media query only: would ignore the user's explicit toggle.
- A separate `ThemeProvider` context: overkill given Zustand is already managing this.

### D4: `AppLayout` wraps all routes — replace bare `<Navbar />` + `<Router />` in App.tsx

**Decision**: Create `shared/components/layout/AppLayout.tsx` that renders `<Navbar>`, conditionally renders `<Sidebar>` (when `sidebarOpen`), wraps `children` in a `<main>`, and renders `<Footer>`. Update `App.tsx` to use `<AppLayout><Router /></AppLayout>` and remove the standalone `<Navbar />`.

**Rationale**: Centralises layout concerns. Pages remain unaware of the shell. Sidebar visibility is driven by the existing `uiStore.sidebarOpen` — no new state needed.

### D5: Sidebar is an overlay on mobile, persistent on `lg:` and above

**Decision**: On mobile (`< lg`), Sidebar overlays with a backdrop and closes on backdrop click or `Escape`. On `lg+`, Sidebar is a fixed-width left panel that pushes `<main>` content using CSS flexbox (`flex-row` on parent, sidebar has `w-64 shrink-0`).

**Rationale**: Standard responsive sidebar pattern. Mobile overlay avoids layout shift on small screens. The `uiStore.sidebarOpen` flag controls both; on `lg+` it defaults to `true` via a `useEffect` that checks `window.matchMedia('(min-width: 1024px)')`.

### D6: Atomic primitives — no Radix, accessible with native HTML + ARIA

**Decision**: Build Button, Input, Card, Badge, Skeleton with semantic HTML only. Build Modal with `<dialog>` native element (or a `role="dialog"` div with `aria-modal`) and manual focus trap.

**Rationale**: Radix is not yet installed; adding it just for Modal adds significant dependency weight. The native `<dialog>` element has excellent built-in accessibility. A minimal focus-trap hook (`useFocusTrap`) can be implemented inline. If Radix is added later, the Modal API can be swapped transparently.

### D7: Extend `Navbar.tsx` in-place — do not replace

**Decision**: Modify the existing `Navbar.tsx` to add the hamburger `<button>` (calls `toggleSidebar`) and a theme-toggle button. Keep all existing auth/role/`useNavLinks` logic intact.

**Rationale**: The AGENTS.md rule is "extender, no reemplazar". The existing Navbar already has the right imports and patterns. Adding two buttons is a small, safe diff.

## Risks / Trade-offs

- **Risk: `clsx`/`tailwind-merge` bundle size** → Both are tiny (~1KB each). Negligible impact.
- **Risk: Native `<dialog>` browser support gaps** → All modern browsers support it. IE11 is not a target. If a polyfill is needed, it can be added transparently without API changes.
- **Risk: Dark-mode flash on load (FOUC)** → `uiStore` rehydrates from localStorage via Zustand `persist`. The `_hasHydrated` flag means we must apply the `.dark` class after hydration. This may cause a brief flash. Mitigation: add an inline script in `index.html` that reads `localStorage['food-store-ui']` and applies `.dark` before React mounts.
- **Risk: `useNavLinks` called in both Navbar and Sidebar** → The hook is pure (no side effects), so double-calling is safe. Each call reads from `useAuthStore` and returns a derived array. No duplication of state.
- **Risk: Over-engineering component API surface** → Keep props minimal. Resist adding every possible variant upfront. Components can be extended when needed.

## Migration Plan

1. Install `clsx` and `tailwind-merge` — `npm install clsx tailwind-merge` in `frontend/`
2. Add `@theme` tokens + `.dark` overrides to `index.css`
3. Create `shared/lib/utils.ts` with `cn()`
4. Create atomic components in `shared/components/ui/`
5. Create layout components in `shared/components/layout/`
6. Extend `Navbar.tsx` (hamburger + theme toggle)
7. Update `App.tsx` — wrap with `AppLayout`, add theme-class effect
8. Write vitest tests
9. Run `npx vitest run` + `npm run lint` — fix any issues
10. Manual smoke test: toggle sidebar, toggle theme, check all routes still render

**Rollback**: The change is purely additive except for `App.tsx` and `Navbar.tsx`. Both have Git history for easy revert. No backend changes, no migrations.

## Open Questions

- Should the `Footer` include navigation links (e.g., "Contacto", "Términos")? → Deferred to content team; implement a minimal copyright footer for now.
- Should `Modal` use native `<dialog>` or `role="dialog"` div? → Use native `<dialog>` with `showModal()` for best accessibility; fallback to polyfill if QA finds issues.
