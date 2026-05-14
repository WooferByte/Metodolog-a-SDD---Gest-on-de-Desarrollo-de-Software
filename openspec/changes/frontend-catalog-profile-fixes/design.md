## Context

**Current state of affected files:**

- `frontend/src/shared/api/axios.ts`: The response interceptor extracts `rfcDetail` via `(error.response.data as Partial<ApiError>)?.detail` and passes it directly to `getErrorMessage(status, rfcDetail)`. `getErrorMessage` returns `{ message: detail ?? mapped.message, type }` — where `detail` could be anything from the backend: a string, an array, or a nested object. `addToast({ message, type })` then stores whatever value was returned. `ToastContainer` renders `{toast.message}` inside a `<p>` — React crashes if `toast.message` is not a primitive.

- `frontend/src/features/profile/components/ChangePasswordForm.tsx`: `validate()` includes `else if (nuevaPassword === passwordActual) { newErrors.nuevaPassword = 'La nueva contraseña debe ser diferente a la actual.' }`. This client-side check prevents the request from reaching the backend even when the user has typed a genuinely different new password but made a typo in the "current password" field. The backend 400 error for wrong current password already triggers an Axios interceptor toast.

- `frontend/src/pages/Catalog.tsx`: Uses `grid grid-cols-1 md:grid-cols-4`. On mobile, the first grid child is the `FilterBar` wrapper div (`md:col-span-1`). Even when the filter panel is hidden (via `hidden/block` inside `FilterBar`), the wrapper `<div>` in the grid still occupies a full-width row slot, pushing products below it, creating an empty visual gap on mobile.

- `frontend/src/features/products/components/FilterBar.tsx`: The hamburger toggle and the `<aside>` panel are siblings in a fragment. The `<aside>` uses `hidden md:block` which correctly hides it on mobile when `isOpen=false`. However there is a structural mismatch: the `<aside>` has `md:w-64` which is ignored on mobile — fine — but the mobile backdrop overlay is `fixed inset-0`, and it appears as a separate element in the DOM flow that can cause z-index conflicts with the product grid area.

- `frontend/src/features/products/components/CategoryFilter.tsx` and `AllergenFilter.tsx`: Use raw utility classes (`text-sm`, `text-foreground`, `text-muted-foreground`) without section-level visual separation, no `border-b border-border` separator between filter groups, no consistent `px-0 py-4` section rhythm, and the checkbox inputs rely on browser defaults without explicit Tailwind ring styling on mobile.

**Constraints:**
- No new npm dependencies (Radix, shadcn not installed)
- Tailwind v4 CSS-first — no `tailwind.config.ts`, use `@theme` tokens only
- React 18 (not 19) — `forwardRef` still required
- vitest + @testing-library/react for tests

---

## Goals / Non-Goals

**Goals:**
- Guarantee `toast.message` is always a string before it reaches React's render tree
- Remove the same-password equality client-side check in `ChangePasswordForm`
- Fix the mobile layout so the filter does not occupy grid space when collapsed
- Apply design-system token classes and visual hierarchy to filter components
- All existing tests continue to pass; new tests cover the fixed behaviours

**Non-Goals:**
- Redesigning the entire catalog page layout
- Installing Radix UI or shadcn/ui components
- Adding dark mode toggle
- Backend changes of any kind
- Changing the toast auto-dismiss durations or max limit

---

## Decisions

### D-1: Where to normalise the toast message — interceptor layer, not component layer

**Decision**: Normalise in `axios.ts` inside `getErrorMessage()` (or a wrapper called just before `addToast`), not inside `ToastContainer`.

**Rationale**: `ToastContainer` is a pure render component and should not contain business logic. The interceptor is the single entry point for all error toasts from API calls. Normalising there means any path that calls `addToast` from the interceptor is safe. `ToastContainer` can add a belt-and-suspenders fallback `String(toast.message)` for manual callers.

**Implementation**:
```ts
// In axios.ts, replace the rfcDetail extraction with:
function safeString(value: unknown): string | undefined {
  if (value === undefined || value === null) return undefined
  if (typeof value === 'string') return value
  if (typeof value === 'object' && 'detail' in (value as object)) {
    return safeString((value as Record<string, unknown>).detail)
  }
  return JSON.stringify(value)
}

// Usage in interceptor:
const rfcDetail = safeString((error.response.data as Partial<ApiError>)?.detail)
```

**Alternative considered**: Fix in `ToastContainer` with `String(toast.message)` — rejected because it treats the symptom not the cause and would hide future bugs in `addToast` callers.

---

### D-2: Remove same-password equality check entirely (not replace with debounced check)

**Decision**: Delete the `else if (nuevaPassword === passwordActual)` branch from `validate()`. No replacement client-side check.

**Rationale**: The backend is the only entity that knows whether the `password_actual` field actually matches the stored hash. A client-side string comparison of what the user typed provides false security — if the user mistyped `passwordActual`, the strings differ, and the request goes through, and the backend returns 400 anyway. Conversely, if both fields happen to be the same string but it is legitimately a new password (edge case: user forgot they already changed it), the client would incorrectly block a valid request. The `onError` path is already handled by the Axios interceptor toast.

**Alternative considered**: Keep the check but only show it as a warning (non-blocking) — rejected as this adds UI complexity for zero security benefit.

---

### D-3: Fix mobile catalog layout by removing the filter from the grid flow

**Decision**: In `Catalog.tsx`, wrap the `FilterBar` in a `<div>` that is `hidden md:block md:col-span-1` so on mobile the entire column is removed from the grid flow. The mobile hamburger button is moved **outside** the grid, above it, as a standalone row.

**Rationale**: The current approach puts the FilterBar inside the `md:grid-cols-4` grid as `md:col-span-1`. On mobile the grid is `grid-cols-1`, so both filter and products are stacked. Even with `FilterBar`'s internal `hidden/block`, the container `<div>` in the grid still occupies a full row. Moving the trigger outside the grid and collapsing the column removes the empty gap.

**Layout structure (mobile):**
```
[mobile-filter-trigger-row]   ← outside grid, full width
[grid cols-1]
  [products col — full width]
```

**Layout structure (desktop):**
```
[grid cols-4]
  [filter col — 1/4]   [products col — 3/4]
```

**The mobile filter panel** opens as a fixed overlay (already implemented via backdrop `fixed inset-0`), positioned via absolute/fixed on top of the grid — no layout disruption.

**Alternative considered**: Make the filter panel a bottom sheet on mobile — rejected as it requires more UI work without clear UX gain.

---

### D-4: Visual hierarchy of filter components — add separators and heading tokens

**Decision**: In `FilterBar`, add `<hr className="border-border" />` between each filter section. In `CategoryFilter` and `AllergenFilter`, convert section headings from `<label>` to semantic `<h3 className="text-sm font-semibold text-foreground">` or `<legend>` inside `<fieldset>`. Apply `gap-4` and `py-3` rhythms. Checkbox inputs get `accent-primary` class.

**Rationale**: The existing components use semantic classes (`text-foreground`, `border-border`) but lack visual separation between sections. A simple `<hr>` separator and consistent padding creates professional visual hierarchy without additional dependencies.

**Alternative considered**: Use background colour blocks per section — rejected as it is heavier styling that may not suit the card background.

---

## Risks / Trade-offs

- **[Risk] `safeString` is called on `error.response.data?.detail`**: If backend changes the RFC 7807 shape (e.g. omits `detail`), `safeString` returns `undefined` and `getErrorMessage` falls back to the mapped message — this is correct behaviour.
- **[Risk] Removing same-password check breaks a test**: `ChangePasswordForm.test.tsx` likely has a test case for "same password is rejected". That test must be updated to verify the check is intentionally absent and that the backend error path shows the server toast instead. Acceptable — the test was testing wrong behaviour.
- **[Risk] Mobile catalog layout shift**: Moving the hamburger trigger outside the grid means it appears above the `AppliedFilters` bar on mobile. This needs to be visually verified. Mitigation: order the mobile trigger after `AppliedFilters` to match the original visual stack.
- **[Trade-off] `String(toast.message)` fallback in ToastContainer**: Adding `String()` in `ToastContainer` as belt-and-suspenders converts `[object Object]` to a visible but non-crashing string. Preferable to a crash, but indicates an upstream bug if it ever fires.

---

## Migration Plan

1. Fix `axios.ts` (BUG 1) — no API changes, purely internal normalisation
2. Fix `ChangePasswordForm.tsx` (BUG 2) — remove one validation branch; update test
3. Fix `Catalog.tsx` + `FilterBar.tsx` layout (BUG 3) — CSS/layout only
4. Apply design tokens to `CategoryFilter.tsx` + `AllergenFilter.tsx` (PROBLEMA 4)
5. Run `npx vitest run` — all tests must pass
6. Manual smoke test: change password with wrong current password, verify toast shows string not crash; resize viewport, verify filter collapses cleanly

No rollback strategy needed — all changes are frontend-only, no data migrations.

## Open Questions

- None. All decisions made based on code exploration and bug reproduction steps provided.
