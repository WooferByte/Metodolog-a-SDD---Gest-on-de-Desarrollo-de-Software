# Food Store Frontend

React + Vite + TypeScript frontend for the Food Store SDD project.

## Project Overview

This is the frontend layer of the Food Store e-commerce platform, built with:
- **React 18+** - UI framework with hooks and concurrent features
- **Vite 5+** - Lightning-fast build tool and dev server
- **TypeScript 5+** - Type-safe JavaScript with strict mode enabled
- **React Router v6** - Client-side routing with protected routes
- **TanStack Query** - Server state management (data fetching, caching)
- **Zustand** - Client state management (UI, preferences)
- **Tailwind CSS v4** - Utility-first CSS framework
- **Axios** - HTTP client for API communication

## Project Structure

Follows **Feature-Sliced Design (FSD)** architecture:

```
frontend/
├── index.html              # Entry HTML file
├── src/
│   ├── main.tsx           # React entry point
│   ├── index.css          # Global styles (Tailwind)
│   ├── app/               # Application layer
│   │   ├── App.tsx        # Root component (providers)
│   │   ├── Router.tsx     # Route configuration
│   │   └── ErrorBoundary.tsx  # Global error boundary
│   ├── pages/             # Page components (one per route)
│   │   ├── Catalog.tsx    # Product catalog
│   │   ├── Login.tsx      # Authentication
│   │   ├── Register.tsx   # User registration
│   │   ├── Profile.tsx    # User profile (protected)
│   │   ├── Orders.tsx     # Order history (protected)
│   │   ├── Admin.tsx      # Admin panel (ADMIN only)
│   │   └── NotFound.tsx   # 404 page
│   ├── features/          # Feature modules (to be implemented)
│   ├── entities/          # Domain entities (to be implemented)
│   ├── widgets/           # Reusable complex components (to be implemented)
│   └── shared/            # Shared infrastructure
│       ├── api/           # HTTP client factory
│       │   └── axios.ts
│       ├── config/        # Configuration
│       │   └── queryClient.ts
│       ├── routing/       # Route guards
│       │   └── withAuth.tsx
│       ├── ui/            # UI component library (to be implemented)
│       └── constants/     # App-wide constants
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── postcss.config.js      # PostCSS configuration
├── package.json           # Dependencies and scripts
└── .env.example           # Environment variables template
```

## Getting Started

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+ or yarn/pnpm

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at **http://localhost:5173** with hot module replacement enabled.

## Available Scripts

### Development
```bash
npm run dev
```
Starts the Vite dev server on port 5173 with HMR (hot module reload).

### Building
```bash
npm run build
```
Builds the application for production to `dist/` folder with source maps.

### Preview Production Build
```bash
npm run preview
```
Serves the production build locally for testing.

### Type Checking
```bash
npm run type-check
```
Runs TypeScript compiler in check-only mode (does not emit files).

## Environment Variables

All environment variables must start with `VITE_` to be accessible in the browser.

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |
| `VITE_ENV` | Environment name | `development`, `staging`, `production` |
| `VITE_MP_PUBLIC_KEY` | MercadoPago public key | `TEST-xxx...` |

**Note**: Environment variables are loaded at **build time**, not runtime. To use different values for different deployments, rebuild the application with the appropriate `.env*` file.

## Routing

### Public Routes
- `/` - Product catalog
- `/login` - User login
- `/register` - User registration

### Protected Routes
- `/profile` - User profile (requires authentication)
- `/orders` - Order history (requires authentication)
- `/admin/*` - Admin panel (requires ADMIN role)

Protected routes use the `withAuth` HOC which will redirect to `/login` if the user is not authenticated.

## Key Features

### 1. Type Safety
- Strict TypeScript mode enabled
- No implicit `any` types allowed
- Unused variables/parameters trigger errors

### 2. Performance
- Path aliases (`@/`) for cleaner imports
- Lazy code splitting (to be implemented in future changes)
- Automatic request deduplication with TanStack Query
- 5-minute cache by default for fresh data

### 3. Error Handling
- Global error boundary for React errors
- Axios interceptor setup for API errors (to be enhanced in future changes)
- Developer-friendly error messages in dev mode

### 4. Styling
- Tailwind CSS v4 with utility-first approach
- Responsive design (mobile-first)
- Dark mode support (to be implemented)

## Architecture Decisions

### Why Vite?
- **Fast**: Native ES modules in development, optimized builds
- **HMR**: Near-instant hot module replacement
- **Plugins**: Extensive ecosystem for React, TypeScript, Tailwind, etc.

### Why React Router v6?
- **Modern API**: Hooks-based, composable routes
- **Data Loading**: Built-in support for data fetching (future enhancement)
- **Type Safety**: Full TypeScript support

### Why TanStack Query?
- **Caching**: Automatic request deduplication and cache management
- **Sync**: Keeps client state synchronized with server
- **Dev Tools**: Redux DevTools integration for debugging

### Why Zustand?
- **Minimal**: Small bundle size, no boilerplate
- **TypeScript**: Excellent type inference
- **Flexible**: Middleware for persistence, devtools, etc.

### Why Tailwind CSS?
- **Utility-First**: No CSS specificity wars
- **Customizable**: Comprehensive theming system
- **Production-Ready**: Automatic CSS purging reduces bundle size

## Error Boundary

The global error boundary catches React component rendering errors and displays a fallback UI. It does NOT catch:
- Event handler errors (use try/catch)
- Async errors (use .catch() or try/catch)
- SSR errors (not applicable for Vite SPA)

For more granular error handling, implement error boundaries at feature/page level.

## Development Workflow

1. **Development**: Run `npm run dev` for instant HMR
2. **Type Checking**: Run `npm run type-check` before committing
3. **Building**: Run `npm run build` to verify production build
4. **Deployment**: Deploy `dist/` folder to CDN or web server

## Next Steps

See CHANGE 6+ for:
- Zustand store setup (auth, cart, UI state)
- Feature implementations (product catalog, checkout, etc.)
- UI component library
- Authentication flow
- Payment integration with MercadoPago

## Troubleshooting

### "Cannot find module '@/...'"
- Verify path aliases in `vite.config.ts` and `tsconfig.json`
- Restart Vite dev server

### "VITE_API_BASE_URL is undefined"
- Ensure `.env` file exists in `frontend/` directory
- Restart Vite dev server

### TypeScript errors on `import.meta.env`
- Add `/// <reference types="vite/client" />` at top of file if needed

## Contributing

- Follow conventional commit messages (feat:, fix:, docs:, etc.)
- Run `npm run type-check` before committing
- Ensure no unused variables or imports

## License

Internal - Food Store SDD Project
