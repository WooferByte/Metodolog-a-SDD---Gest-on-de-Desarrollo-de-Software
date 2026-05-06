# Tasks: frontend-react-vite-setup

Implementation checklist for CHANGE 5 (frontend-react-vite-setup). Each task should be completed in order and verified against the spec.

---

## 1. Project Scaffolding and Dependencies

- [ ] 1.1 Create `frontend/package.json` with project metadata (name, version, type: module)
- [ ] 1.2 Add React + React-DOM dependencies (v18+) to package.json
- [ ] 1.3 Add Vite and @vitejs/plugin-react to devDependencies
- [ ] 1.4 Add TypeScript and @types/react, @types/react-dom to devDependencies
- [ ] 1.5 Add Tailwind CSS, PostCSS, and autoprefixer to devDependencies
- [ ] 1.6 Add React Router (react-router-dom v6+) dependency
- [ ] 1.7 Add TanStack Query (@tanstack/react-query v4+) dependency
- [ ] 1.8 Add Axios (axios v1+) dependency
- [ ] 1.9 Add Zustand (zustand v4+) dependency
- [ ] 1.10 Add @mercadopago/sdk-js dependency
- [ ] 1.11 Add recharts for charts support
- [ ] 1.12 Add lucide-react for icons
- [ ] 1.13 Run `npm install` and verify node_modules is created
- [ ] 1.14 Verify `package-lock.json` is generated

---

## 2. Vite Configuration

- [ ] 2.1 Create `frontend/vite.config.ts` with React plugin
- [ ] 2.2 Configure path alias: `@` → `src/`
- [ ] 2.3 Configure dev server to listen on port 5173
- [ ] 2.4 Enable CORS for dev server
- [ ] 2.5 Configure build output with minification
- [ ] 2.6 Add source maps for development builds
- [ ] 2.7 Test Vite config: `npm run dev` starts successfully

---

## 3. TypeScript Configuration

- [ ] 3.1 Create `frontend/tsconfig.json` with `strict: true`
- [ ] 3.2 Enable `noUnusedLocals: true` in TypeScript config
- [ ] 3.3 Enable `noUnusedParameters: true` in TypeScript config
- [ ] 3.4 Set `target: "ES2020"` for modern JavaScript
- [ ] 3.5 Set `moduleResolution: "bundler"` for Vite compatibility
- [ ] 3.6 Configure `jsx: "react-jsx"` for automatic JSX transform
- [ ] 3.7 Add path mapping for `@/` alias in tsconfig
- [ ] 3.8 Create `tsconfig.app.json` for app-specific settings (if needed)
- [ ] 3.9 Verify TypeScript compilation: `npm run type-check` passes

---

## 4. Tailwind CSS Configuration

- [ ] 4.1 Create `frontend/tailwind.config.js` with content paths
- [ ] 4.2 Configure theme with default Tailwind colors
- [ ] 4.3 Add brand colors if available (placeholder for future)
- [ ] 4.4 Configure responsive breakpoints (sm, md, lg, xl, 2xl)
- [ ] 4.5 Set up typography settings (fonts, sizes, line heights)
- [ ] 4.6 Create `frontend/postcss.config.js` with Tailwind + autoprefixer
- [ ] 4.7 Create `frontend/src/index.css` with Tailwind directives (@tailwind)
- [ ] 4.8 Test Tailwind: Create temp component with class `bg-blue-500` and verify styling

---

## 5. File Structure and Entry Points

- [ ] 5.1 Create `frontend/index.html` with root div id="root"
- [ ] 5.2 Create `frontend/src/main.tsx` as entry point
- [ ] 5.3 Create `frontend/src/app/App.tsx` root component
- [ ] 5.4 Create `frontend/src/app/Router.tsx` route definitions
- [ ] 5.5 Create `frontend/src/app/ErrorBoundary.tsx` error boundary component
- [ ] 5.6 Verify file structure matches FSD layout (app/, pages/, features/, entities/, widgets/, shared/)

---

## 6. Shared API Infrastructure

- [ ] 6.1 Create `frontend/src/shared/api/` directory
- [ ] 6.2 Create `frontend/src/shared/api/axios.ts` with Axios client factory
- [ ] 6.3 Configure Axios to read `VITE_API_BASE_URL` from environment
- [ ] 6.4 Set default request headers in Axios (Content-Type)
- [ ] 6.5 Export singleton Axios instance for app-wide use
- [ ] 6.6 Add response interceptor hook (placeholder for auth in CHANGE 7)
- [ ] 6.7 Test Axios client: Import and verify it has `get`, `post`, `put`, `delete` methods

---

## 7. TanStack Query Configuration

- [ ] 7.1 Create `frontend/src/shared/config/` directory
- [ ] 7.2 Create `frontend/src/shared/config/queryClient.ts`
- [ ] 7.3 Configure QueryClient with `staleTime: 5 minutes`
- [ ] 7.4 Configure QueryClient with `gcTime: 10 minutes`
- [ ] 7.5 Configure QueryClient with `retry: 1`
- [ ] 7.6 Configure QueryClient with `refetchOnWindowFocus: true`
- [ ] 7.7 Export QueryClient instance for provider mounting

---

## 8. React Router Setup

- [ ] 8.1 Create `frontend/src/shared/routing/` directory
- [ ] 8.2 Create `frontend/src/shared/routing/withAuth.tsx` HOC for route protection
- [ ] 8.3 Implement withAuth: Check `authStore.isAuthenticated` (placeholder)
- [ ] 8.4 Implement withAuth: Redirect to /login if not authenticated
- [ ] 8.5 Implement withAuth: Accept optional `requiredRoles` parameter
- [ ] 8.6 Implement withAuth: Show 403 screen if role insufficient
- [ ] 8.7 Implement withAuth: Preserve props typing with TypeScript generics
- [ ] 8.8 Test withAuth HOC: Wrap a component and verify type checking works

---

## 9. App Root Component and Providers

- [ ] 9.1 Implement `frontend/src/app/App.tsx` as root component
- [ ] 9.2 Wrap App with QueryClientProvider (from TanStack Query)
- [ ] 9.3 Wrap App with BrowserRouter (from React Router)
- [ ] 9.4 Wrap App with ErrorBoundary component
- [ ] 9.5 Render Router component inside providers
- [ ] 9.6 Test provider nesting: Verify no console errors on app load

---

## 10. Error Boundary Component

- [ ] 10.1 Implement `frontend/src/app/ErrorBoundary.tsx` as React.Component class
- [ ] 10.2 Implement `getDerivedStateFromError()` to update state on error
- [ ] 10.3 Implement `componentDidCatch()` to log errors
- [ ] 10.4 Display error message and stack trace in development mode
- [ ] 10.5 Display friendly error message in production mode
- [ ] 10.6 Add "Reload Page" button in error UI
- [ ] 10.7 Test Error Boundary: Throw error in child component and verify fallback UI

---

## 11. Router Component

- [ ] 11.1 Implement `frontend/src/app/Router.tsx` with route definitions
- [ ] 11.2 Add public route: `GET /` → Catalog page (placeholder)
- [ ] 11.3 Add public route: `GET /login` → Login page (placeholder)
- [ ] 11.4 Add public route: `GET /register` → Register page (placeholder)
- [ ] 11.5 Add private route: `GET /profile` → User Profile (protected with withAuth)
- [ ] 11.6 Add private route: `GET /orders` → My Orders (protected with withAuth)
- [ ] 11.7 Add admin route: `GET /admin/*` → Admin Panel (protected with withAuth(['ADMIN']))
- [ ] 11.8 Add fallback route: `*` → Redirect to / or 404 page
- [ ] 11.9 Test routing: Navigate to each route and verify correct component renders

---

## 12. Environment Variables

- [ ] 12.1 Create `frontend/.env.example` file
- [ ] 12.2 Add `VITE_API_BASE_URL=http://localhost:8000` to .env.example
- [ ] 12.3 Add `VITE_ENV=development` to .env.example
- [ ] 12.4 Add `VITE_MP_PUBLIC_KEY=YOUR_MERCADOPAGO_PUBLIC_KEY` to .env.example
- [ ] 12.5 Add comments explaining each variable
- [ ] 12.6 Create `frontend/.env` (local) from .env.example
- [ ] 12.7 Verify environment variables are accessible via `import.meta.env.VITE_*`

---

## 13. npm Scripts

- [ ] 13.1 Add `npm run dev` script: `vite`
- [ ] 13.2 Add `npm run build` script: `tsc && vite build`
- [ ] 13.3 Add `npm run preview` script: `vite preview`
- [ ] 13.4 Add `npm run type-check` script: `tsc --noEmit`
- [ ] 13.5 Test `npm run dev`: Server starts on port 5173
- [ ] 13.6 Test `npm run build`: Creates `dist/` folder with optimized output
- [ ] 13.7 Test `npm run type-check`: Passes with no errors

---

## 14. Placeholder Components

- [ ] 14.1 Create `frontend/src/pages/Catalog.tsx` (empty, for routing)
- [ ] 14.2 Create `frontend/src/pages/Login.tsx` (empty, for routing)
- [ ] 14.3 Create `frontend/src/pages/Register.tsx` (empty, for routing)
- [ ] 14.4 Create `frontend/src/pages/Profile.tsx` (empty, for routing)
- [ ] 14.5 Create `frontend/src/pages/Orders.tsx` (empty, for routing)
- [ ] 14.6 Create `frontend/src/pages/NotFound.tsx` (empty, for routing)
- [ ] 14.7 Create `frontend/src/pages/Admin.tsx` (empty, for routing)

---

## 15. Documentation

- [ ] 15.1 Create `frontend/README.md` with project description
- [ ] 15.2 Add "Getting Started" section with setup instructions
- [ ] 15.3 Add "Development" section explaining `npm run dev`
- [ ] 15.4 Add "Building for Production" section explaining `npm run build`
- [ ] 15.5 Add "Environment Variables" section with explanation
- [ ] 15.6 Add "Project Structure" section describing FSD layout
- [ ] 15.7 Add "Architecture Decisions" section referencing design.md

---

## 16. Verification and Testing

- [ ] 16.1 Run `npm run dev` and verify app loads on http://localhost:5173
- [ ] 16.2 Verify Vite HMR works: Edit a component and see live reload
- [ ] 16.3 Run `npm run type-check`: Verify no TypeScript errors
- [ ] 16.4 Run `npm run build`: Verify production build succeeds and creates `dist/`
- [ ] 16.5 Run `npm run preview`: Verify production build can be served locally
- [ ] 16.6 Verify path aliases work: Import using `@/shared/api/axios`
- [ ] 16.7 Verify Tailwind CSS works: Add a component with `className="text-2xl font-bold"`
- [ ] 16.8 Verify error boundary: Throw intentional error and see fallback UI
- [ ] 16.9 Verify Router: Navigate between routes and verify correct component renders
- [ ] 16.10 Verify environment variables: Console log `import.meta.env.VITE_API_BASE_URL` and see correct URL

---

## 17. Git and Commit

- [ ] 17.1 Create checkpoint commit: "feat: CHANGE 5 initial scaffolding (frontend structure, deps, configs)"
- [ ] 17.2 Create feature commit: "feat(frontend): implement Vite + React + TypeScript setup"
- [ ] 17.3 Create feature commit: "feat(frontend): implement error boundary, router, providers"
- [ ] 17.4 Create feature commit: "feat(frontend): implement Axios and QueryClient configuration"
- [ ] 17.5 Create feature commit: "docs: add frontend README and environment documentation"
- [ ] 17.6 Verify all commits follow conventional commit format
- [ ] 17.7 Verify git log shows logical progression of changes

---

## Summary

**Total Tasks**: 114 checkboxes across 17 groups

**Estimated Time**: 3-4 hours (depending on developer familiarity with Vite, React Router, TanStack Query)

**Validation**: All tasks should be completed before archiving. Each task is verifiable via:
- File creation/modification
- npm script execution
- Console output verification
- Browser testing
- TypeScript compilation
- Git commit history

**Next Change**: CHANGE 6 (frontend-zustand-stores-setup) depends on this foundation being complete.
