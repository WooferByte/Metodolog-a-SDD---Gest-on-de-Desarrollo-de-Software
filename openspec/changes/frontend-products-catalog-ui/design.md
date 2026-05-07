## Context

The FoodStore frontend already has:
- React 18 + Vite + TypeScript strict mode (CHANGE 5)
- React Router v6 with public/private routes (CHANGE 5)
- TanStack Query (React Query) configured for API calls (CHANGE 5)
- Zustand stores for auth, cart, payment, ui (CHANGE 8)
- Tailwind CSS v4 + PostCSS configured (CHANGE 5)
- Axios interceptor setup with JWT handling (part of CHANGE 5 integration)

Backend APIs ready:
- `GET /api/v1/productos` — public endpoint with filters (categoria, busqueda, excluirAlergenos, page, limit)
- `GET /api/v1/productos/:id` — public endpoint for product detail
- `GET /api/v1/categorias` — public endpoint returning hierarchical categories

The catalog page is currently a placeholder. This change implements the complete UI.

## Goals / Non-Goals

**Goals:**
- Render a responsive product grid (mobile-first) on the `/catalog` page
- Implement real-time search with debounce (250ms)
- Support filtering by: category (multi-select), allergen exclusion (checkboxes)
- Display product details in a modal (ProductDetail component)
- Integrate with cartStore to add items with quantity selector
- Show skeleton loaders while fetching
- Implement pagination (20 items/page)
- Ensure WCAG 2.1 AA accessibility (alt text, aria labels, keyboard nav)
- Use Tailwind CSS v4 for all styling (no inline styles)
- Support mobile, tablet, and desktop viewports

**Non-Goals:**
- Advanced analytics or tracking (will be added in a later change)
- Wishlist functionality (future feature)
- Product reviews/ratings (separate change)
- Infinite scroll (pagination is sufficient)
- Server-side search analytics

## Decisions

### 1. Component Structure: Container + Presentational

**Decision**: Use container/presenter pattern for Catalog
- **Presenter**: CatalogPage component (handles routing, UI layout)
- **Container**: CatalogContainer component (handles API calls, filters, state)

**Rationale**: Separates concerns (API logic vs UI rendering), easier testing, simpler component reuse

**Alternatives considered**:
- Hook-based architecture: simpler but mixes logic and UI in one component
- State management in Zustand: overkill for local UI state (search, current page, filters)

### 2. API Call Strategy: React Query

**Decision**: Use TanStack Query (React Query) for all API calls via custom hooks
- Hook: `useProductsCatalog(filters, page, limit)` returns `{ data, isPending, isError, error, refetch }`
- Automatic caching, retry on 5xx, stale-while-revalidate

**Rationale**: Already installed (CHANGE 5), handles loading/error states automatically, avoids redundant API calls

**Alternatives considered**:
- Direct axios calls: requires manual loading/error state management
- GraphQL: introduces new complexity, not yet in stack

### 3. Filter State Management

**Decision**: Keep filter state local to CatalogContainer (React hooks, not Zustand)
- State: `{ categoryIds: [], search: string, excludeAllergens: [], currentPage: 1 }`
- Debounce search input (250ms) before triggering API call

**Rationale**: Filters are ephemeral UI state, not persistent across sessions. Zustand is for persistent state (auth, cart)

**Alternatives considered**:
- URL query params: adds complexity, enables bookmarking/sharing (nice-to-have, can be added later)
- Zustand: overcomplicates state, pollutes cart/auth store

### 4. ProductCard + ProductDetail Modal

**Decision**: Two separate components
- **ProductCard**: Thumbnail display (image, name, price, "View Details" button, "Add to Cart" button)
- **ProductDetail**: Full-screen modal with description, ingredients, allergen indicators, quantity selector, add-to-cart action

**Rationale**: ProductCard is reusable (can be used in other pages), modal separates detail view from grid

**Alternatives considered**:
- Single expandable card: clutters grid, poor UX
- Slide-out drawer: adds routing complexity

### 5. Pagination vs Infinite Scroll

**Decision**: Use pagination with page buttons (1, 2, 3... Next, Previous)
- 20 items per page (backend default from CHANGES.md)
- Total count shown

**Rationale**: Simpler, works better on mobile, predictable performance

**Alternatives considered**:
- Infinite scroll: requires intersection observer, harder to implement with React Query

### 6. Allergen Exclusion UI

**Decision**: Checkbox list in filter sidebar
- Show list of all allergen ingredients
- User can check "exclude this allergen"
- When clicked, filter API calls with `excluirAlergenos=1,3,7` (IDs)

**Rationale**: Explicit control, important for safety

**Alternatives considered**:
- Toggle button: less discoverable
- Pop-over dropdown: takes up sidebar space

### 7. Styling Approach

**Decision**: Tailwind CSS v4 utility classes
- Component variants via `clsx` or `classnames` utility
- CSS Variables for theme tokens (colors, spacing from Tailwind config)

**Rationale**: Already configured (CHANGE 5), no additional dependencies

**Alternatives considered**:
- CSS Modules: added complexity
- Styled Components: runtime overhead

### 8. Mobile Responsiveness

**Decision**: Mobile-first breakpoints (Tailwind defaults: sm, md, lg, xl)
- ProductCard: 1 col on mobile, 2 on tablet, 3-4 on desktop
- Filter sidebar: collapsible on mobile (hamburger menu)
- Modal: full-width on mobile, centered on desktop

**Rationale**: Tailwind built-in, better performance than media query JS

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Slow catalog page load** → Large product list (100+) with images | Implement pagination (20 items/page), lazy-load images with Intersection Observer |
| **API timeout on slow networks** → Mobile users experience blank screen | Show skeleton loaders, implement request timeout (5s), allow user to retry |
| **Allergen filter incorrect** → User clicks allergen checkbox, forgets it's applied | Display applied filters visually (e.g., "Excluding: peanuts, dairy"), "Clear all" button |
| **Product modal slow to render** → Modal shows details from separate API call | Use prefetch on ProductCard hover, cache detail in React Query |
| **Accessibility issues** → Screen reader users can't navigate filters | Use semantic HTML (fieldset, legend), aria-labels on all inputs, keyboard tab navigation |
| **Category hierarchy deep** → Dropdown too long | Implement search-in-dropdown, limit to 2 levels of nesting |

## Migration Plan

1. **Phase 1**: Create CatalogPage + CatalogContainer skeleton
2. **Phase 2**: Implement ProductCard + ProductList grid
3. **Phase 3**: Implement filter logic (category, search, allergens)
4. **Phase 4**: Implement ProductDetail modal + add-to-cart integration
5. **Phase 5**: Add skeleton loaders + error handling
6. **Phase 6**: Test accessibility + responsive design on devices
7. **Phase 7**: Deploy and monitor performance

## Open Questions

1. Should we prefetch product details when user hovers over ProductCard? (Performance vs UX trade-off)
2. Should applied filters persist in URL query params for shareable links? (Nice-to-have, can be a future enhancement)
3. What's the expected performance SLA for catalog load (< 2s, < 3s)?
