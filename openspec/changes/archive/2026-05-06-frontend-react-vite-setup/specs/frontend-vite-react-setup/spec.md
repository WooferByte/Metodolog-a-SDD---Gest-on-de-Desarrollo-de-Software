# Spec: frontend-vite-react-setup

## ADDED Requirements

### Requirement: Project scaffolding with Node.js and npm

The system SHALL provide a Node.js project with `package.json` that declares all frontend dependencies, scripts, and metadata.

#### Scenario: Install dependencies from package.json
- **WHEN** developer runs `npm install` in the `frontend/` directory
- **THEN** all declared dependencies are downloaded and node_modules/ is created
- **AND** a `package-lock.json` is generated for reproducible installs

#### Scenario: Run development server
- **WHEN** developer runs `npm run dev`
- **THEN** Vite dev server starts on `http://localhost:5173`
- **AND** hot module reloading (HMR) is active for `.tsx` file changes
- **AND** the browser automatically refreshes when files change

#### Scenario: Build for production
- **WHEN** developer runs `npm run build`
- **THEN** TypeScript is transpiled and bundled to `frontend/dist/`
- **AND** CSS is minified and optimized
- **AND** JavaScript is minified and tree-shaken for unused code removal

### Requirement: Vite configuration for React development

The system SHALL provide a `vite.config.ts` that configures the build tool for React + TypeScript development with path aliases and multi-environment support.

#### Scenario: Path alias resolution
- **WHEN** code imports from `@/shared/api/axios`
- **THEN** Vite resolves this to `src/shared/api/axios`
- **AND** TypeScript IDE autocomplete recognizes the alias

#### Scenario: React Fast Refresh enabled
- **WHEN** developer edits a React component and saves
- **THEN** Vite hot-reloads the component without full page refresh
- **AND** component state is preserved during reload (if possible)

#### Scenario: Environment-specific dev server
- **WHEN** the dev server starts
- **THEN** it listens on port `5173`
- **AND** CORS is enabled for requests to `http://localhost:8000` (backend)

### Requirement: TypeScript strict configuration

The system SHALL configure TypeScript with strict type checking enabled, including checks for unused variables and parameters.

#### Scenario: Strict mode enforces types
- **WHEN** code has implicit `any` types or missing type annotations
- **THEN** TypeScript compiler reports an error
- **AND** developer must add explicit types or ignore errors with `// @ts-ignore`

#### Scenario: Unused variables detected
- **WHEN** code declares a variable that is never referenced
- **THEN** TypeScript compiler reports "unused variable" error
- **AND** build fails until variable is used or prefixed with `_`

#### Scenario: Unused function parameters detected
- **WHEN** code declares a function parameter that is never used
- **THEN** TypeScript compiler reports "unused parameter" error
- **AND** build fails until parameter is used or prefixed with `_`

#### Scenario: Correct TypeScript types pass
- **WHEN** code has explicit types and no unused variables
- **THEN** `npm run type-check` completes successfully
- **AND** no errors are reported

### Requirement: Tailwind CSS integration with PostCSS

The system SHALL provide Tailwind CSS configuration for styling with support for design tokens and responsive design.

#### Scenario: Tailwind classes work in components
- **WHEN** a React component uses Tailwind classes (e.g., `className="bg-blue-500"`)
- **THEN** the CSS is generated and applied correctly in the browser
- **AND** styles are optimized (only used classes included in production build)

#### Scenario: Responsive design works
- **WHEN** a component uses responsive classes (e.g., `className="md:text-lg"`)
- **THEN** styling changes at the `md` breakpoint (≥768px)
- **AND** mobile-first approach is maintained

#### Scenario: PostCSS processing pipeline
- **WHEN** `npm run build` runs
- **THEN** PostCSS processes all CSS files
- **AND** Tailwind directives are expanded into utility classes
- **AND** unused CSS is purged before minification

### Requirement: Axios HTTP client configured

The system SHALL provide a configured Axios instance that reads the API base URL from environment variables and is ready for HTTP requests.

#### Scenario: Environment-aware base URL
- **WHEN** code imports the Axios client from `@/shared/api/axios`
- **THEN** the client uses `VITE_API_BASE_URL` from the environment
- **AND** in development it points to `http://localhost:8000`
- **AND** in production it points to the backend server URL from env file

#### Scenario: Default request headers set
- **WHEN** Axios client makes a request
- **THEN** `Content-Type: application/json` header is automatically set
- **AND** request/response interceptor hooks are available for future use

#### Scenario: Axios client is testable
- **WHEN** unit tests need to mock API calls
- **THEN** the Axios client can be mocked or replaced with a test double
- **AND** no axios instances are created inside components (only from factory)

### Requirement: TanStack Query (React Query) client configured

The system SHALL provide a QueryClient with production-ready default settings for data fetching and caching.

#### Scenario: QueryClient with sensible defaults
- **WHEN** the app initializes
- **THEN** QueryClient is configured with:
  - `staleTime: 5 minutes` (data considered fresh for 5 min)
  - `gcTime: 10 minutes` (cached data garbage collected after 10 min)
  - `retry: 1` (failed requests retried once)
  - `refetchOnWindowFocus: true` (data refetched when browser tab regains focus)

#### Scenario: QueryClient mounted at app root
- **WHEN** the app starts
- **THEN** QueryClientProvider wraps all child components
- **AND** useQuery, useMutation, and other hooks are available throughout the app

#### Scenario: Queries cached intelligently
- **WHEN** two components request the same data (same query key)
- **THEN** second component receives cached data immediately
- **AND** network request is not duplicated

### Requirement: React Router with public and private routes

The system SHALL provide a routing structure with public routes (accessible without login) and private routes (protected by authentication).

#### Scenario: Public routes accessible
- **WHEN** user navigates to `/` (catalog)
- **THEN** page loads without requiring authentication
- **AND** no redirect to login occurs

#### Scenario: Private routes protected
- **WHEN** user is not authenticated and navigates to `/profile`
- **THEN** user is redirected to `/login`
- **AND** `/profile` is not rendered

#### Scenario: Route definitions centralized
- **WHEN** developer needs to add a new route
- **THEN** route can be added in `app/Router.tsx` in a centralized location
- **AND** all routes are visible in one file

### Requirement: Route protection via HOC

The system SHALL provide a `withAuth` higher-order component (HOC) that protects routes by checking authentication status.

#### Scenario: withAuth HOC requires authentication
- **WHEN** a component is wrapped with `withAuth(Component)`
- **THEN** the component is only rendered if user is authenticated
- **AND** unauthenticated users see a redirect to login

#### Scenario: withAuth HOC checks roles
- **WHEN** a component is wrapped with `withAuth(Component, ['ADMIN'])`
- **THEN** the component is only rendered if user has the ADMIN role
- **AND** users without ADMIN role see a 403 forbidden screen

#### Scenario: withAuth HOC passes through props
- **WHEN** the wrapped component has props
- **THEN** props are passed through to the component correctly
- **AND** TypeScript generics preserve prop typing

### Requirement: Global error boundary

The system SHALL provide an Error Boundary component that catches React rendering errors and displays a fallback UI.

#### Scenario: React rendering error caught
- **WHEN** a component throws an error during render
- **THEN** Error Boundary catches it and prevents app crash
- **AND** fallback UI is displayed to user
- **AND** error details are logged to console

#### Scenario: Error boundary displays development info
- **WHEN** app is in development mode and an error occurs
- **THEN** error message and stack trace are displayed
- **AND** developer can see where the error originated

#### Scenario: Error boundary displays production info
- **WHEN** app is in production mode and an error occurs
- **THEN** friendly error message is shown ("Something went wrong")
- **AND** stack trace is not exposed
- **AND** error is logged for monitoring

#### Scenario: Reload button recovers app
- **WHEN** error boundary is displaying and user clicks "Reload"
- **THEN** page is reloaded
- **AND** app attempts to recover from the error state

### Requirement: Environment variable configuration

The system SHALL provide a `.env.example` file documenting all frontend environment variables with sensible defaults.

#### Scenario: .env.example includes required variables
- **WHEN** developer reads `.env.example`
- **THEN** it includes `VITE_API_BASE_URL`, `VITE_ENV`, and `VITE_MP_PUBLIC_KEY`
- **AND** each variable has a comment explaining its purpose

#### Scenario: Environment variables are used at build time
- **WHEN** `npm run build` runs with `.env.production`
- **THEN** environment variables are read during the build
- **AND** hardcoded into the JavaScript bundle
- **AND** cannot be changed after build without rebuilding

#### Scenario: Development environment defaults
- **WHEN** developer creates `.env` locally
- **THEN** `VITE_API_BASE_URL` defaults to `http://localhost:8000`
- **AND** `VITE_ENV` defaults to `development`

### Requirement: npm scripts for common tasks

The system SHALL provide npm scripts for development, building, and type checking.

#### Scenario: npm run dev starts dev server
- **WHEN** developer runs `npm run dev` in `frontend/` directory
- **THEN** Vite dev server starts on port 5173
- **AND** terminal shows "Local: http://localhost:5173"

#### Scenario: npm run build creates production bundle
- **WHEN** developer runs `npm run build`
- **THEN** TypeScript is checked and transpiled
- **AND** output is in `frontend/dist/`
- **AND** all CSS and JS are minified

#### Scenario: npm run type-check validates TypeScript
- **WHEN** developer runs `npm run type-check`
- **THEN** TypeScript compiler runs in check-only mode
- **AND** no JavaScript is emitted
- **AND** build script can exit early if types fail

#### Scenario: npm run preview serves production build locally
- **WHEN** developer runs `npm run preview`
- **THEN** the `dist/` folder is served on a local port
- **AND** developer can test production build behavior

### Requirement: FSD folder structure initialized

The system SHALL establish the Feature-Sliced Design (FSD) folder structure with appropriate subdirectories for app organization.

#### Scenario: FSD directories exist
- **WHEN** developer lists `frontend/src/` contents
- **THEN** the following directories exist:
  - `app/` — root application layer
  - `pages/` — page components
  - `features/` — feature modules
  - `entities/` — domain entities
  - `widgets/` — reusable complex components
  - `shared/` — shared infrastructure
- **AND** each directory has appropriate subdirectories (api, ui, config, etc.)

#### Scenario: Import paths follow FSD conventions
- **WHEN** code needs to use a shared utility
- **THEN** it imports from `@/shared/...` not `../../shared/...`
- **AND** code follows relative import minimization

#### Scenario: Lazy loading support for features
- **WHEN** feature modules are in `features/` with their own components
- **THEN** they can be lazy-loaded using `React.lazy()` in Router
- **AND** code splitting is optimized for production

### Requirement: Main entry point and providers

The system SHALL provide `main.tsx` that mounts the React app with all required providers.

#### Scenario: React app mounts at #root element
- **WHEN** `main.tsx` runs
- **THEN** React app is mounted to the `#root` element in `index.html`
- **AND** StrictMode is enabled for development warnings

#### Scenario: Providers are stacked correctly
- **WHEN** the app initializes
- **THEN** providers are nested in order: ErrorBoundary → QueryClientProvider → BrowserRouter
- **AND** each provider wraps its children correctly

#### Scenario: App component renders Router
- **WHEN** React renders the app
- **THEN** `<App>` component renders `<Router>` component
- **AND** routes are evaluated and matched

---

## Summary

This spec defines the complete frontend scaffolding for React + TypeScript + Vite, including configuration files, build tooling, routing, and error handling. All scenarios are testable and can be verified by running the provided npm scripts.
