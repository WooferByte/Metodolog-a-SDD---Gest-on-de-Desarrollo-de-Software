# Proposal: frontend-react-vite-setup

## Why

Food Store backend infrastructure (CHANGE 2-4) is complete and production-ready. The frontend is the client-facing layer that enables users to browse products, manage carts, place orders, and track deliveries. Without a properly scaffolded React + TypeScript + Vite environment, we cannot build the UI features defined in EPIC 02-11.

CHANGE 5 establishes the frontend foundation: project structure, dev tooling, routing architecture, API client setup, state management hooks, and error handling — all aligned with Feature-Sliced Design (FSD) and production-ready patterns.

## What Changes

- **Project scaffolding**: Create `package.json` with all dependencies (React, Vite, TypeScript, Tailwind, React Router, TanStack Query, Zustand, Axios, MercadoPago SDK)
- **Vite configuration**: Multi-environment support, path aliases (`@/`), TypeScript strict mode with `noUnusedLocals` and `noUnusedParameters`, dev server on port 5173
- **TypeScript configuration**: `strict: true` + aggressive unused checks for code quality
- **Tailwind CSS + PostCSS**: Design system foundation with brand colors (if available) + extensible defaults
- **Core infrastructure**:
  - `shared/api/axios.ts` — Axios client factory with multi-environment `VITE_API_BASE_URL`
  - `shared/config/queryClient.ts` — TanStack QueryClient with production defaults (staleTime: 5m, retry: 1)
  - `shared/routing/withAuth.tsx` — Route guard HOC for role-based access
  - `app/App.tsx` — Root component with QueryClientProvider, BrowserRouter, Error Boundary
  - `app/Router.tsx` — Route definitions (public + private)
  - `app/ErrorBoundary.tsx` — Global error boundary for React errors
- **.env.example**: Multi-environment variables (`VITE_API_BASE_URL`, `VITE_ENV`, `VITE_MP_PUBLIC_KEY`)
- **npm scripts**: `dev` (Vite dev server), `build` (production build), `preview`, `type-check`
- **FSD alignment**: Reinforce the already-created FSD folder structure with initial infrastructure

## Capabilities

### New Capabilities

- `frontend-vite-react-setup`: Vite + React + TypeScript scaffolding with strict mode and multi-environment support
- `frontend-axios-client`: Configurable Axios HTTP client with base URL from environment
- `frontend-tanstack-query-setup`: TanStack Query client with production-ready defaults
- `frontend-routing-architecture`: React Router v6 with public/private route HOCs and FSD alignment
- `frontend-error-boundary`: Global error boundary for React component error handling
- `frontend-tailwind-design-system`: Tailwind CSS + PostCSS with brand colors and extensible design tokens
- `frontend-typescript-strict-config`: TypeScript strict mode with aggressive unused checks

### Modified Capabilities

(none — CHANGE 5 is pure new frontend infrastructure)

## Impact

- **Frontend codebase**: Creates `/frontend` as a functioning React application (dev and production builds)
- **Dependencies**: Adds ~25 npm packages (React, Vite, TypeScript, Tailwind, routers, API clients, query clients)
- **Dev experience**: Enables hot module reloading (HMR), type checking in IDE, linting hooks
- **Architecture**: Establishes patterns that all future frontend changes (CHANGE 6+) depend on:
  - How to import utilities (`@/` path aliases)
  - How to fetch data (Axios + QueryClient)
  - How to protect routes (withAuth HOC)
  - How to handle errors (Error Boundary)
  - How to structure components (FSD)
- **Backward compatibility**: No breaking changes (first frontend implementation)
- **APIs**: No backend API changes needed (uses existing `/api/v1` endpoints from backend)

---

**Status**: Ready for Design & Specs phase  
**Depends on**: `infrastructure-repo-setup` ✅, `backend-fastapi-core-setup` ✅  
**Unlocks**: CHANGE 6 (`frontend-zustand-stores-setup`), CHANGE 7+ (frontend feature changes)
