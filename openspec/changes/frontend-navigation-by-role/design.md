## Context

`Navbar.tsx` already exists at `shared/components/Navbar.tsx` but uses inline styles and has no role awareness. `authStore` (Zustand v5) already exposes `isAuthenticated`, `user.roles: string[]`, and `hasRole(role)`. Router.tsx and all pages exist — this change only touches the navigation layer.

Stack constraints: Tailwind **v4** (`@tailwindcss/postcss`, no config file), Zustand **v5**, imports via `@/` path alias, tests with **vitest** (not jest).

## Goals / Non-Goals

**Goals:**
- Render role-specific nav links from a single `useNavLinks` hook
- Tailwind v4 styling for the Navbar (replace all inline styles)
- 5 vitest unit tests covering every auth state

**Non-Goals:**
- New pages or routes
- Sidebar / mobile hamburger menu (out of scope for this change)
- Active-link highlighting (nice-to-have, deferred)
- Backend changes

## Decisions

**Decision 1 — `useNavLinks` hook separates logic from rendering**
The hook returns a typed array of `{ label, to }` objects. Navbar maps over it. This makes the role logic independently testable without mounting the component.

**Decision 2 — Role link sets**
```
Unauthenticated : Catálogo /catalog · Iniciar sesión /login · Registrarse /register
CLIENT          : Catálogo /catalog · Carrito /cart · Mis Pedidos /orders · Mi Perfil /profile · Mis Direcciones /addresses
STOCK           : Productos /admin/productos · Categorías /admin/categorias · Ingredientes /admin/ingredientes
PEDIDOS         : Panel Pedidos /admin/pedidos
ADMIN           : Catálogo /catalog · Mis Pedidos /orders · Usuarios /admin/usuarios · Pedidos /admin/pedidos · Métricas /admin/metricas · Configuración /admin/configuracion
```
ADMIN gets full access. When a user has ADMIN role they see the admin superset. Role priority (first match): ADMIN → PEDIDOS → STOCK → CLIENT → unauthenticated.

**Decision 3 — Tailwind v4 class utilities only, no arbitrary inline styles**
Navbar uses utility classes like `bg-gray-900 text-white flex items-center px-6 py-3 gap-4`. No `style={{}}` props anywhere in the new component.

**Decision 4 — `_hasHydrated` guard**
Navbar reads from `useAuthStore`. To avoid flash of wrong nav on first render, check `_hasHydrated` before rendering role-specific links — show a neutral skeleton or the public links until hydration completes.

## Risks / Trade-offs

`user.roles` may be empty after login if `setUser` wasn't called with role data → Mitigation: `useNavLinks` defaults to unauthenticated links when `user === null` or `user.roles.length === 0`.

Routes like `/cart` and `/addresses` don't have pages yet → Mitigation: Link to them anyway (they'll hit the 404 page); adding pages is a future change. This is standard for nav-first development.
