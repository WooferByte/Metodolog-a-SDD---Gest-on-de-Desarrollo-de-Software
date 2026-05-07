/**
 * Hook: useCategoriesHierarchy
 * 
 * Fetches hierarchical product categories from API
 * Used to populate category filter dropdown
 * 
 * Usage:
 * ```tsx
 * const { data: categories, isPending } = useCategoriesHierarchy()
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { axiosInstance } from '@/shared/api/axios'
import type { CategoriesApiResponse } from '@/features/products/types'
import { API_ENDPOINTS, QUERY_KEYS, API_TIMEOUT } from '@/features/products/constants'

/**
 * useCategoriesHierarchy Hook
 * 
 * Fetches categories on component mount
 * - Long cache (30 minutes) since categories rarely change
 * - Minimal retry (categories are relatively stable)
 * 
 * @returns Query state: { data, isPending, isError, error }
 */
export function useCategoriesHierarchy() {
  return useQuery<CategoriesApiResponse>({
    queryKey: [QUERY_KEYS.CATEGORIES],
    queryFn: async () => {
      const response = await axiosInstance.get<CategoriesApiResponse>(
        API_ENDPOINTS.CATEGORIES,
        { timeout: API_TIMEOUT },
      )
      return response.data
    },
    // Long cache since categories are stable
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 60 * 60 * 1000, // 60 minutes
    
    // Retry strategy
    retry: 2,
  })
}

/**
 * Helper: Build category hierarchy from flat list
 * Separates parent categories from children
 * 
 * @param categories - Flat list from API
 * @returns Object with categorized structure
 */
export function buildCategoryHierarchy(categories: CategoriesApiResponse) {
  return {
    parents: categories.filter((c) => !c.padre_id),
    children: categories.filter((c) => c.padre_id),
    getChildren: (parentId: string) => 
      categories.filter((c) => c.padre_id === parentId),
  }
}
