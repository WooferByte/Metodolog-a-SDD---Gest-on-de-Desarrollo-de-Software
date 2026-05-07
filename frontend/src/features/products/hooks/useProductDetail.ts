/**
 * Hook: useProductDetail
 * 
 * Fetches detailed information for a single product
 * Used when opening ProductDetail modal
 * 
 * Usage:
 * ```tsx
 * const { data: product, isPending, isError } = useProductDetail(productId)
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { axiosInstance } from '@/shared/api/axios'
import type { Product } from '@/features/products/types'
import { API_ENDPOINTS, QUERY_KEYS, API_TIMEOUT } from '@/features/products/constants'

/**
 * useProductDetail Hook
 * 
 * Fetches a single product by ID from the API
 * - Disabled if productId is not provided
 * - Cached for 10 minutes
 * - No automatic retry on 4xx errors
 * 
 * @param productId - ID of product to fetch (optional)
 * @returns Query state: { data, isPending, isError, error }
 */
export function useProductDetail(productId?: string) {
  return useQuery<Product>({
    queryKey: [QUERY_KEYS.PRODUCT_DETAIL, productId],
    queryFn: async () => {
      if (!productId) {
        throw new Error('Product ID is required')
      }
      const response = await axiosInstance.get<Product>(
        API_ENDPOINTS.PRODUCT_DETAIL(productId),
        { timeout: API_TIMEOUT },
      )
      return response.data
    },
    // Only fetch if productId is provided
    enabled: !!productId,
    
    // Caching strategy
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    
    // Minimal retry
    retry: 1,
  })
}
