import { useEffect, lazy, Suspense } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/shared/config/queryClient'
import { ErrorBoundary } from '@/app/ErrorBoundary'
import Router from '@/app/Router'
import { AppLayout } from '@/shared/components/layout'
import { ToastContainer } from '@/shared/components/ToastContainer'
import { useUIStore } from '@/store/uiStore'

// CartDrawer is lazy-loaded — it only initializes when first opened (bundle-dynamic-imports)
const CartDrawer = lazy(() =>
  import('@/widgets/CartDrawer').then((m) => ({ default: m.CartDrawer }))
)

/**
 * Root Application Component
 *
 * Mounts all global providers, error boundary, and the AppLayout shell.
 *
 * Dark mode:
 *   Subscribes to uiStore.theme and applies/removes the 'dark' class on
 *   document.documentElement. The @custom-variant in index.css activates
 *   all .dark token overrides when this class is present.
 *
 * Layout:
 *   AppLayout wraps Router so all routes share Navbar + Sidebar + Footer.
 *   ToastContainer renders outside <main> (inside AppLayout or at App root)
 *   so toasts float above page content regardless of route.
 */
export default function App() {
  const theme = useUIStore((s) => s.theme)

  // Apply/remove dark class on <html> when theme changes
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppLayout>
            <Router />
          </AppLayout>
          {/* CartDrawer — global overlay, outside <Routes> so it persists across route changes */}
          <Suspense fallback={null}>
            <CartDrawer />
          </Suspense>
          {/* ToastContainer rendered outside <main> — floats over all content */}
          <ToastContainer />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
