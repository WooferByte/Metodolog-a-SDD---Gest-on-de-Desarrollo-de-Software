/**
 * Product Catalog Constants
 * 
 * Configuration constants for:
 * - API limits and timeouts
 * - UI behavior (debounce, animations)
 * - Default values
 */

/** Number of products to display per page */
export const ITEMS_PER_PAGE = 20

/** Debounce delay for search input (milliseconds) */
export const SEARCH_DEBOUNCE_DELAY = 250

/** API request timeout (milliseconds) */
export const API_TIMEOUT = 5000

/** Maximum quantity per item in cart */
export const MAX_QUANTITY = 999

/** Minimum quantity per item in cart */
export const MIN_QUANTITY = 1

/** Toast notification duration (milliseconds) */
export const TOAST_DURATION = 3000

/**
 * Image loading strategy
 * Using native lazy loading attribute
 */
export const IMAGE_LOADING = 'lazy' as const

/**
 * Responsive grid breakpoints (Tailwind CSS)
 * Mobile: 1 col, Tablet: 2 cols, Desktop: 3-4 cols
 */
export const GRID_CLASSES = {
  container: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
  skeleton: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
}

/**
 * API endpoints
 */
export const API_ENDPOINTS = {
  PRODUCTS: '/api/v1/productos',
  PRODUCT_DETAIL: (id: string) => `/api/v1/productos/${id}`,
  CATEGORIES: '/api/v1/categorias',
} as const

/**
 * Query keys for React Query caching
 */
export const QUERY_KEYS = {
  PRODUCTS: 'products',
  PRODUCT_DETAIL: 'productDetail',
  CATEGORIES: 'categories',
} as const

/**
 * Error messages
 */
export const ERROR_MESSAGES = {
  LOAD_FAILED: 'Failed to load products. Please try again.',
  NO_INTERNET: 'No internet connection',
  TIMEOUT: 'Request timed out. Please try again.',
  NO_PRODUCTS: 'No products found',
  ADD_TO_CART_FAILED: 'Failed to add product to cart',
} as const

/**
 * Success messages
 */
export const SUCCESS_MESSAGES = {
  ADDED_TO_CART: 'Added to cart!',
} as const
