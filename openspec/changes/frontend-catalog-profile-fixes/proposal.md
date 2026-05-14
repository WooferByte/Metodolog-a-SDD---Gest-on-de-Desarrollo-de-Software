## Why

Manual testing of `frontend-user-profile-ui` (EPIC 06) revealed 4 defects: a React render crash when backend RFC 7807 errors reach the ToastContainer as objects, a client-side password comparison that bypasses the backend's authoritative validation, broken responsive layout in the product catalog on mobile viewports, and a filter panel that lacks visual hierarchy and accessible markup. These issues block real-world usability and must be corrected before moving to EPIC 07.

## What Changes

- **BUG 1 — Toast object crash**: The Axios interceptor extracts `rfcDetail` from `error.response.data.detail` (a string) and passes it to `addToast`. However, for some 400 responses the backend returns the `detail` field as a nested object or the entire body is passed as-is, causing React to throw "Objects are not valid as a React child" when rendering `toast.message` inside `<p>`. Fix: add a `safeString()` normaliser in the interceptor that coerces any non-string value to a string (e.g. `JSON.stringify`) before calling `addToast`.
- **BUG 2 — Client-side password comparison removed**: `ChangePasswordForm` validates `nuevaPassword !== passwordActual` client-side and surfaces that error before hitting the server. This is incorrect: the backend returns 400 when the current password is wrong, and it is the sole authority on what constitutes a valid password change. Remove the `nuevaPassword === passwordActual` client-side check; keep only format checks (required, min-length). Server errors (400 RFC 7807) are already handled by the Axios interceptor toast.
- **BUG 3 — Catalog responsive layout**: On mobile, `FilterBar` uses `display:none / display:block` toggled by a hamburger button, but the parent grid in `Catalog.tsx` uses `grid-cols-1 md:grid-cols-4`, which on mobile stacks filter above products — the filter occupies a full-width row even when collapsed. Fix: on mobile the filter panel must not occupy layout space when closed (`hidden` class with `md:block`); the hamburger toggle floats above the product grid (position or overlay approach), and the backdrop overlay already exists. Adjust the grid so that on mobile only the product column is visible by default.
- **PROBLEMA 4 — Filter panel visual design**: `CategoryFilter` and `AllergenFilter` are styled as plain text labels without section headers, separators, or consistent spacing tokens from `tailwind-design-system`. Fix: apply `@theme` semantic tokens (`text-foreground`, `text-muted-foreground`, `border-border`, `bg-card`, `bg-muted`), add `<hr>` separators between filter sections inside `FilterBar`, improve checkbox label spacing and hover states, add section heading typography hierarchy.

## Capabilities

### New Capabilities

- `toast-error-normalisation`: Ensures the `message` field passed to `addToast` is always a primitive string, preventing React render crashes from RFC 7807 object payloads.

### Modified Capabilities

- `catalog-filter-ui`: Responsive layout and visual design of the `FilterBar`, `CategoryFilter`, and `AllergenFilter` components are changing to meet mobile-first breakpoints and design system token standards.
- `change-password-form`: Validation logic in `ChangePasswordForm` is changing — the same-password client-side check is removed; only format checks remain; server is the sole authority on password correctness.

## Impact

- `frontend/src/shared/api/axios.ts` — add `safeString()` normaliser; update call to `getErrorMessage`
- `frontend/src/shared/components/ToastContainer.tsx` — defensive string check on `toast.message` as belt-and-suspenders
- `frontend/src/features/profile/components/ChangePasswordForm.tsx` — remove same-password equality check
- `frontend/src/pages/Catalog.tsx` — adjust mobile layout to prevent filter from taking up collapsed space
- `frontend/src/features/products/components/FilterBar.tsx` — responsive overlay approach, section separators, design tokens
- `frontend/src/features/products/components/CategoryFilter.tsx` — design token classes, section heading, accessible markup improvements
- `frontend/src/features/products/components/AllergenFilter.tsx` — design token classes, spacing, accessible markup improvements
- No backend changes, no new dependencies, no migrations
