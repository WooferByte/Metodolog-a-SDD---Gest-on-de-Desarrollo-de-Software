/**
 * Hook: useProductsCatalog
 * 
 * Fetches paginated products with filters (category, search, allergens)
 * Uses React Query for caching, retries, and state management
 * 
 * Usage:
 * ```tsx
 * const { data, isPending, isError, error, refetch } = useProductsCatalog(
 *   { categoryIds: ['1'], search: 'pizza', excludeAllergens: [], currentPage: 1 },
 *   20
 * )
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { axiosInstance } from '@/shared/api/axios'
import type { ProductsApiResponse, CatalogFilters } from '@/features/products/types'
import { ITEMS_PER_PAGE, API_ENDPOINTS, QUERY_KEYS, API_TIMEOUT } from '@/features/products/constants'

/**
 * Build query parameters for products API
 */
function buildProductsQueryParams(filters: CatalogFilters, size: number): URLSearchParams {
  const params = new URLSearchParams()

  if (filters.categoryIds.length > 0) {
    params.append('categoria_id', filters.categoryIds[0])
  }

  if (filters.search.trim()) {
    params.append('q', filters.search.trim())
  }

  params.append('page', String(filters.currentPage))
  params.append('size', String(size))

  return params
}

/**
 * useProductsCatalog Hook
 * 
 * Handles all product catalog fetching with React Query
 * - Automatic retry on failure
 * - Caching with stale-while-revalidate strategy
 * - Loading and error states
 * 
 * @param filters - Current filter state
 * @param limit - Items per page (default: 20)
 * @returns Query state: { data, isPending, isError, error, refetch, isFetching }
 */
export function useProductsCatalog(
  filters: CatalogFilters,
  size: number = ITEMS_PER_PAGE,
) {
  const queryParams = buildProductsQueryParams(filters, size)
  const queryUrl = `${API_ENDPOINTS.PRODUCTS}?${queryParams.toString()}`

  return useQuery<ProductsApiResponse>({
    queryKey: [QUERY_KEYS.PRODUCTS, filters],
    queryFn: async () => {
      const response = await axiosInstance.get<ProductsApiResponse>(queryUrl, {
        timeout: API_TIMEOUT,
      })
      return response.data
    },
    // Caching strategy
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    
    // Retry strategy
    retry: (failureCount, error: unknown) => {
      // Don't retry on 4xx errors (except timeout)
      const axiosError = error as { response?: { status?: number } }
      if (axiosError?.response?.status && axiosError.response.status < 500 && axiosError.response.status !== 408) {
        return false
      }
      // Retry up to 2 times on 5xx or network errors
      return failureCount < 2
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}
