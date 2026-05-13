# Design: frontend-user-profile-ui

## Architecture Overview

This is a **frontend-only** change. No backend modifications. The feature lives in a new `features/profile/` directory following FSD conventions. The existing `pages/Profile.tsx` stub is replaced with a page that composes feature components.

```
Pages
  └── Profile.tsx          ← replaces stub; composes feature components
        │
Features
  └── profile/
        ├── hooks/
        │   ├── usePerfil.ts          ← TanStack Query — GET /api/v1/perfil
        │   ├── useUpdatePerfil.ts    ← TanStack Query mutation — PUT /api/v1/perfil
        │   └── useCambiarPassword.ts ← TanStack Query mutation — POST /perfil/cambiar-password
        ├── components/
        │   ├── ProfileInfo.tsx       ← read-only profile card (email, roles, member since)
        │   ├── EditProfileForm.tsx   ← form: nombre + telefono
        │   └── ChangePasswordForm.tsx← form: password_actual + nueva_password
        └── types/
            └── profile.ts            ← PerfilData, UpdatePerfilPayload, ChangePasswordPayload
        │
Shared (reuse only — no changes)
  ├── components/ui/Button, Input, Card, Skeleton, Badge
  └── api/axios (apiClient singleton)
```

## State Management Decision

**Rule**: TanStack Query owns all server state. Zustand owns client-only state. Profile data MUST NOT be duplicated in Zustand.

| Data | Where it lives | Why |
|------|---------------|-----|
| `UsuarioResponse` (perfil from API) | TanStack Query cache | Server state — fetched per session, stale after mutations |
| `user.email` for display | `authStore.user.email` | Already in Zustand from login — read-only, no duplication |
| Form input values | Local `useState` in each form component | Ephemeral — no need for global state |
| Loading/submitting flags | TanStack Query `isPending` | Part of mutation state |

No new Zustand stores or slices required.

## Data Flow

```
Profile.tsx
  │
  ├── usePerfil()         → GET /api/v1/perfil → { data, isLoading, error }
  │   └── staleTime: 60s, placeholderData: keepPreviousData
  │
  ├── useUpdatePerfil()   → PUT /api/v1/perfil
  │   └── onSuccess: invalidate ['perfil'] query → refetch
  │
  └── useCambiarPassword()→ POST /api/v1/perfil/cambiar-password
      └── onSuccess: toast "Contraseña actualizada" → setTimeout 2000ms → authStore.logout()
```

## Component Design

### `Profile.tsx` (Page)

```tsx
// Responsive layout: mobile = single column, desktop = 2-column grid
<main aria-label="Mi Perfil">
  <h1>Mi Perfil</h1>
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <ProfileInfo />                 {/* read-only: email, nombre, telefono, roles, member since */}
    <div className="flex flex-col gap-6">
      <EditProfileForm />           {/* edit nombre + telefono */}
      <ChangePasswordForm />        {/* change password */}
    </div>
  </div>
</main>
```

### `ProfileInfo.tsx`

Displays data from `usePerfil()`. While loading, renders `Skeleton` placeholders (prevents layout shift). Uses `Badge` for each role. Shows `creado_en` formatted as `DD/MM/YYYY`. Also shows `user.email` from `authStore` (static — no duplication, just read).

```
<Card>
  <CardHeader>
    <CardTitle>Información de cuenta</CardTitle>
  </CardHeader>
  <CardContent>
    Email: {authStore.user.email}      ← from Zustand (static)
    Nombre: {perfil.nombre}            ← from TanStack Query
    Teléfono: {perfil.telefono}        ← from TanStack Query
    Roles: <Badge> per role            ← from TanStack Query
    Miembro desde: {formatted date}    ← from TanStack Query
  </CardContent>
</Card>
```

ARIA: `<section aria-labelledby>` wrapping, skeleton has `aria-busy="true"` during load.

### `EditProfileForm.tsx`

Local state for `nombre` and `telefono`. Client-side validation before mutation:
- At least one field changed (dirty check).
- `nombre`: 1–100 chars if provided.
- `telefono`: max 20 chars if provided.

Uses existing `Input` (has `label`, `error`, `aria-invalid`) and `Button` (has `loading` prop).

On submit: calls `useUpdatePerfil()`. On success: invalidates query, shows success toast via `uiStore.addToast`.

### `ChangePasswordForm.tsx`

Local state for `password_actual` and `nueva_password`. Client-side validation:
- Both fields required, min 8 chars.
- nueva_password ≠ password_actual.

Password inputs: type="password" with show/hide toggle (`aria-pressed` on toggle button, `aria-label` on inputs).

On submit: calls `useCambiarPassword()`. On 204: toast + 2s delay + `authStore.logout()` + navigate to `/login`.

Note: 400 (wrong password), 422, and other errors are handled automatically by the Axios interceptor (RFC 7807 toast) — no extra error handling needed in the component.

### Skeleton loading pattern

```tsx
// While isLoading — no CLS, WCAG: aria-busy
<div aria-busy="true" aria-label="Cargando perfil">
  <Skeleton className="h-5 w-48" />
  <Skeleton className="h-5 w-32" />
  <Skeleton className="h-6 w-24" />  {/* Badge placeholder */}
  <Skeleton className="h-5 w-36" />
</div>
```

## API Hooks Design

### `usePerfil`

```ts
export function usePerfil() {
  return useQuery({
    queryKey: ['perfil'],
    queryFn: () => apiClient.get<PerfilData>('/api/v1/perfil').then(r => r.data),
    staleTime: 60_000,          // 60s — avoid refetch on every focus
    placeholderData: keepPreviousData,  // avoids flicker on window refocus
  })
}
```

### `useUpdatePerfil`

```ts
export function useUpdatePerfil() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdatePerfilPayload) =>
      apiClient.put<PerfilData>('/api/v1/perfil', payload).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['perfil'] })
      useUIStore.getState().addToast({ message: 'Perfil actualizado.', type: 'success' })
    },
  })
}
```

### `useCambiarPassword`

```ts
export function useCambiarPassword() {
  const { logout } = useAuthStore()
  return useMutation({
    mutationFn: (payload: ChangePasswordPayload) =>
      apiClient.post('/api/v1/perfil/cambiar-password', payload),
    onSuccess: () => {
      useUIStore.getState().addToast({
        message: 'Contraseña actualizada. Iniciá sesión nuevamente.',
        type: 'success',
      })
      setTimeout(() => {
        logout()
        // Navigate to /login handled by ProtectedRoute after logout clears auth
      }, 2000)
    },
    // onError: not needed — Axios interceptor handles 400/422 via RFC 7807 toast
  })
}
```

## Types

```ts
// features/profile/types/profile.ts

export interface PerfilData {
  id: number
  email: string
  nombre: string
  telefono: string | null
  roles: string[]
  creado_en: string   // ISO 8601
}

export interface UpdatePerfilPayload {
  nombre?: string
  telefono?: string
}

export interface ChangePasswordPayload {
  password_actual: string
  nueva_password: string
}
```

Note: `AuthStore['user']` has `name` (not `nombre`) and `roles: string[]`. The TanStack Query `PerfilData` is the canonical server representation. We only use `authStore.user.email` for display (avoid re-fetching what's already available client-side — but we do NOT sync `nombre` from the API back to `authStore` — that would duplicate server state).

## Styling Rules (enforced)

All styles use semantic tokens from `index.css` `@theme`:

| Purpose | Token class |
|---------|------------|
| Page background | `bg-background` |
| Card surface | `bg-card text-card-foreground` |
| Borders | `border-border` |
| Input focus ring | `ring-ring` |
| Error/destructive | `text-destructive border-destructive` |
| Muted labels | `text-muted-foreground` |
| Primary button | `bg-primary text-primary-foreground` |
| Role badge success | `bg-success text-success-foreground` |

**Prohibited**: Any raw Tailwind color class (e.g. `bg-gray-900`, `text-blue-600`, `border-zinc-200`).

## Responsive Layout

Mobile-first:
- Single column: `grid-cols-1`
- Desktop breakpoint `lg` (1024px): two columns `lg:grid-cols-2`
- Forms stack vertically within right column: `flex flex-col gap-6`
- Inputs always `w-full`
- Buttons `w-full` on mobile, `w-auto` at `sm:` breakpoint

## Accessibility Checklist

- `<main>` with `aria-label="Mi Perfil"`
- `<h1>` as page heading
- All `<input>` elements have associated `<label>` (via `Input` component's `label` prop → `htmlFor`)
- Error messages use `role="alert"` (via `Input` component's `error` prop)
- Password visibility toggles: `aria-pressed`, `aria-label="Mostrar contraseña"`
- Skeleton loading: `aria-busy="true"` on container
- Form submit buttons: `aria-busy` during `isPending` (via `Button` `loading` prop)
- WCAG AA contrast: guaranteed by OKLCH semantic tokens

## E2E Test Strategy

File: `frontend/e2e/profile/profile.spec.ts`

Scenarios:
1. **Guard**: Unauthenticated → `/profile` redirects to `/login` (no `loginAs`, calls `logout(page)`)
2. **Load**: Authenticated CLIENT → page renders profile data (mock `GET /api/v1/perfil`)
3. **Edit profile**: Fill form → submit → mock `PUT` returns updated data → success toast visible
4. **Password change**: Fill both passwords (valid) → mock returns 204 → toast visible → navigates to `/login`
5. **Password validation error**: nueva_password === password_actual → client-side error, no API call

Pattern: use `loginAs(page, 'CLIENT')` helper (seeds `food-store-auth` in localStorage via `addInitScript`). Mock backend with `page.route`.

## File Locations

```
frontend/src/
  pages/
    Profile.tsx                           ← replace stub
  features/
    profile/
      hooks/
        usePerfil.ts
        useUpdatePerfil.ts
        useCambiarPassword.ts
      components/
        ProfileInfo.tsx
        EditProfileForm.tsx
        ChangePasswordForm.tsx
      types/
        profile.ts
      __tests__/
        usePerfil.test.ts
        EditProfileForm.test.tsx
        ChangePasswordForm.test.tsx

frontend/e2e/
  profile/
    profile.spec.ts
```

## Dependencies — No New Packages Required

All required packages are already installed:
- `@tanstack/react-query` ^5.28.0 — hooks
- `zustand` ^5.0.8 — `authStore` (read-only in this change)
- `lucide-react` ^0.294.0 — eye/eye-off icons for password toggle
- Tailwind v4 — styling
- `vitest` ^3.2.4 — unit tests
- `@playwright/test` — E2E (install if not present: `npm install -D @playwright/test`)
