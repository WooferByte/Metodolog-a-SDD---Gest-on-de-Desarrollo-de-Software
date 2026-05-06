# Design: frontend-react-vite-setup

## Architecture Overview

CHANGE 5 establishes a **multi-layered frontend architecture** aligned with Feature-Sliced Design (FSD) and production-ready patterns:

```
src/
├── app/                    # Root application layer
│   ├── App.tsx            # Root component (providers, error boundary)
│   ├── Router.tsx         # Route configuration (public + private)
│   └── ErrorBoundary.tsx  # Global error boundary
├── pages/                 # Page components (mapped to routes)
├── features/              # Feature modules (checkout, order tracking, etc.)
├── entities/              # Domain entities (user, product, order)
├── widgets/               # Complex reusable components
├── shared/                # Shared infrastructure
│   ├── api/
│   │   └── axios.ts      # Axios client factory
│   ├── config/
│   │   └── queryClient.ts # TanStack QueryClient setup
│   ├── routing/
│   │   └── withAuth.tsx  # Route guard HOC
│   ├── ui/                # Atomic UI components (built in later changes)
│   └── constants/         # App-wide constants
└── main.tsx              # Entry point
```

## Components

### 1. Vite Configuration (`vite.config.ts`)

**Responsibility**: Configures Vite dev server, build output, TypeScript support, and plugin system

**Location**: `frontend/vite.config.ts`

**Details**:
- React plugin: `@vitejs/plugin-react`
- Resolve aliases: `@` → `src/`
- Dev server: port `5173`, CORS enabled for backend
- Build output: minified, source maps in dev
- Environment variables: loaded from `.env*` files
- TypeScript: `ts.esModule` for proper CommonJS interop

**Snippet**:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    cors: true,
  },
})
```

### 2. TypeScript Configuration (`tsconfig.json`)

**Responsibility**: Enforces strict type checking and code quality standards

**Location**: `frontend/tsconfig.json`

**Details**:
- `strict: true` — enables all strict checks
- `noUnusedLocals: true` — error on unused variables
- `noUnusedParameters: true` — error on unused function params
- `noImplicitAny: true` — forbid implicit `any` types
- `target: "ES2020"` — modern JavaScript target
- `moduleResolution: "bundler"` — for Vite compatibility
- `jsx: "react-jsx"` — use React 17+ automatic JSX transform

### 3. Tailwind CSS Configuration (`tailwind.config.js`)

**Responsibility**: Defines design tokens, colors, typography, and responsive breakpoints

**Location**: `frontend/tailwind.config.js`

**Details**:
- **Theme Extension**: Brand colors if available; otherwise use Tailwind defaults with extend pattern
- **Typography**: Configure font families, sizes, line heights for consistency
- **Spacing**: Use Tailwind defaults (already production-proven)
- **Breakpoints**: Mobile-first (sm, md, lg, xl, 2xl)
- **Dark Mode**: Configure (if needed) via `class` strategy

**Strategy**: Keep CHANGE 5 config minimal. Future changes can extend with custom colors, components, plugins.

### 4. Axios Client (`shared/api/axios.ts`)

**Responsibility**: Factory for creating configured Axios instances with environment-aware base URL

**Location**: `frontend/src/shared/api/axios.ts`

**Details**:
- Reads `VITE_API_BASE_URL` from environment
- Sets default headers: `Content-Type: application/json`
- Creates response interceptor placeholder (actual auth interceptor in CHANGE 7)
- Exports singleton client instance for app-wide use
- Testable: client can be mocked for unit tests

**Interface**:
```typescript
export const apiClient = createAxiosClient(
  import.meta.env.VITE_API_BASE_URL
)

// Usage:
const data = await apiClient.get('/api/v1/productos')
```

### 5. QueryClient Setup (`shared/config/queryClient.ts`)

**Responsibility**: Configures TanStack Query with production-ready defaults

**Location**: `frontend/src/shared/config/queryClient.ts`

**Details**:
- `staleTime: 1000 * 60 * 5` — data considered fresh for 5 minutes
- `gcTime: 1000 * 60 * 10` — garbage collect unused queries after 10 minutes
- `retry: 1` — retry failed queries once (no exponential backoff yet)
- `refetchOnWindowFocus: true` — refetch when window regains focus (user returns to tab)

**Rationale**: Balances performance (less refetching) with freshness. Can be tuned per-query in later changes.

### 6. Route Guard HOC (`shared/routing/withAuth.tsx`)

**Responsibility**: Protects routes by requiring authentication and role-based access

**Location**: `frontend/src/shared/routing/withAuth.tsx`

**Details**:
- HOC that wraps components with auth check
- Receives `requiredRoles?: string[]` parameter
- Checks `authStore.isAuthenticated` (will be added in CHANGE 6)
- Redirects to login if not authenticated
- Shows 403 screen if role insufficient
- Usage:
  ```typescript
  export const AdminDashboard = withAuth(AdminDashboardPage, ['ADMIN'])
  ```

### 7. App Root Component (`app/App.tsx`)

**Responsibility**: Mounts all global providers and error boundary

**Location**: `frontend/src/app/App.tsx`

**Details**:
- Wraps with `QueryClientProvider` (TanStack Query)
- Wraps with `BrowserRouter` (React Router)
- Wraps with `ErrorBoundary` (global error handling)
- Renders `Router` component

**Structure**:
```typescript
<ErrorBoundary>
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <Router />
    </BrowserRouter>
  </QueryClientProvider>
</ErrorBoundary>
```

### 8. Router Component (`app/Router.tsx`)

**Responsibility**: Defines all route definitions (public + private) for the app

**Location**: `frontend/src/app/Router.tsx`

**Details**:
- Public routes:
  - `/` → Catalog page
  - `/login` → Login page
  - `/register` → Register page
- Private routes (protected by `withAuth`):
  - `/profile` → User profile (CLIENT+)
  - `/orders` → My orders (CLIENT+)
  - `/admin/*` → Admin panel (ADMIN only)
- Wildcard: `/` (redirect to catalog or 404)

### 9. Error Boundary (`app/ErrorBoundary.tsx`)

**Responsibility**: Catches React component rendering errors and displays fallback UI

**Location**: `frontend/src/app/ErrorBoundary.tsx`

**Details**:
- Extends `React.Component` (required for error boundaries)
- Implements `componentDidCatch()` and `getDerivedStateFromError()`
- Displays error message in dev (with stack trace)
- Displays friendly message in production
- Logs errors to console (can be extended to error tracking service)
- Provides "Reload" button to recover

**Error States Handled**:
- Component render errors (not caught: event handlers, async errors)
- Warnings about bad props (will be converted to errors in CHANGE X if needed)

### 10. Environment Variables (`.env.example`)

**Responsibility**: Documents all frontend environment variables

**Location**: `frontend/.env.example`

**Variables**:
```
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Environment
VITE_ENV=development

# MercadoPago (initialized in later changes)
VITE_MP_PUBLIC_KEY=PKG_MERCADOPAGO_PUBLIC_KEY_HERE
```

**Multi-Environment Strategy**:
- `.env` → local defaults (development)
- `.env.development` → override for dev
- `.env.staging` → staging server URL
- `.env.production` → production server URL
- **Never commit `.env`** — use `.env.example` as template

## Data Model

No database changes. Frontend is a pure client application. State management patterns defined in CHANGE 6 (Zustand stores).

## API Changes

No backend API changes. CHANGE 5 uses existing backend endpoints (created in CHANGE 2-4) via Axios client.

## Implementation Notes

### 1. Path Aliases (`@/`)

Using `@/` instead of `../../../shared/api` keeps imports clean and refactor-safe:

```typescript
// ❌ Bad
import { apiClient } from '../../../shared/api/axios'

// ✅ Good
import { apiClient } from '@/shared/api/axios'
```

### 2. Multi-Environment Support

Environment variables are loaded at **build time** (not runtime). This means:
- Each deployment must run `npm run build` with the correct `.env*` file
- Cannot change `VITE_*` variables after build without rebuilding
- For true runtime config, consider adding a `config.json` served from backend (future improvement)

### 3. Error Boundary Limitations

Error Boundaries do NOT catch:
- Event handler errors (use try/catch in onClick, etc.)
- Async errors (use .catch() or try/catch in async functions)
- SSR errors (n/a for Vite SPA)
- Errors in the error boundary itself

More detailed error handling (network errors, validation errors) handled in CHANGE 7+ via Axios interceptors and React Query error callbacks.

### 4. Provider Order

The nesting order matters:
1. **ErrorBoundary** — outermost (catches all React errors)
2. **QueryClientProvider** — needs to be inside error boundary
3. **BrowserRouter** — must wrap Router component
4. **Router** — renders pages/features

Changing order can cause unexpected behavior (e.g., BrowserRouter outside ErrorBoundary won't catch routing errors).

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| TypeScript strict mode will fail existing code | N/A — CHANGE 5 is new code. Strictness enforced from day 1. |
| Vite dev server crashes if backend is down | Feature in CHANGE 7 (Axios interceptor) will show network error UI. For now, show console error. |
| Race condition if user navigates during Axios request | TanStack Query handles request cancellation automatically. Interceptors in CHANGE 7 will retry intelligently. |
| Error Boundary doesn't catch async errors | Document in README. Use .catch() on promises. Better error handling in later changes. |
| Environment variables not set | Vite will error at build time if `import.meta.env.VITE_API_BASE_URL` is undefined. Mitigates accidentally deploying with wrong config. |
| Tailwind CSS bundle size | Output only used styles. No CSS framework bloat. CSS is ~50KB minified (acceptable). |

## Build & Dev Workflow

**Development**:
```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:5173 with HMR
```

**Production Build**:
```bash
npm run build
# Output in `dist/`
npm run preview
# Serves `dist/` locally for testing
```

**Type Checking**:
```bash
npm run type-check
# Runs `tsc --noEmit` to check types without emitting files
```

---

**Status**: Ready for Specs & Tasks phases  
**Key Decision Points for Later Changes**:
- Zustand stores (CHANGE 6) will integrate with this foundation
- Axios JWT interceptor (CHANGE 7) will extend `shared/api/axios.ts`
- UI components (CHANGE 8+) will extend Tailwind config
