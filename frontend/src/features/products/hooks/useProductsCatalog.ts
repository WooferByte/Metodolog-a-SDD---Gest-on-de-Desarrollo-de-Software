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
function buildProductsQueryParams(filters: CatalogFilters, limit: number): URLSearchParams {
  const params = new URLSearchParams()

  // Add category IDs (comma-separated if multiple)
  if (filters.categoryIds.length > 0) {
    params.append('categoria', filters.categoryIds.join(','))
  }

  // Add search term
  if (filters.search.trim()) {
    params.append('busqueda', filters.search.trim())
  }

  // Add allergen exclusions (comma-separated if multiple)
  if (filters.excludeAllergens.length > 0) {
    params.append('excluirAlergenos', filters.excludeAllergens.join(','))
  }

  // Add pagination
  params.append('page', String(filters.currentPage))
  params.append('limit', String(limit))

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
  limit: number = ITEMS_PER_PAGE,
) {
  const queryParams = buildProductsQueryParams(filters, limit)
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
