import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/shared/config/queryClient'
import { ErrorBoundary } from '@/app/ErrorBoundary'
import Router from '@/app/Router'
import Navbar from '@/shared/components/Navbar'
import { ToastContainer } from '@/shared/components/ToastContainer'

/**
 * Root Application Component
 * Mounts all global providers and error boundary
 */
export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Navbar />
          <Router />
          <ToastContainer />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
