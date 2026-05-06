import { QueryClient } from '@tanstack/react-query'

/**
 * TanStack Query configuration
 * Production-ready defaults for data fetching
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10,   // 10 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
})
