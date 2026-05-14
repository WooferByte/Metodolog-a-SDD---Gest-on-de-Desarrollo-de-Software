/**
 * Product Catalog Type Definitions
 * 
 * Defines all TypeScript interfaces for:
 * - Product data structures
 * - API responses
 * - Component props
 * - Filter state
 */

/**
 * Ingredient - ingredient details with allergen information
 */
export interface Ingredient {
  id: string
  nombre: string
  is_alergeno: boolean // True if ingredient is an allergen
}

/**
 * Category - product category with hierarchical support
 */
export interface Category {
  id: string
  nombre: string
  padre_id?: string | null // Parent category ID for hierarchy
}

/**
 * Product - single product from catalog
 * NOTE: backend sends `precio_base` (ProductoResponse.precio_base) — keep aligned.
 */
export interface Product {
  id: string
  nombre: string
  descripcion: string
  precio_base: number
  imagen_url: string
  disponible: boolean
  stock_cantidad: number
  categorias: Category[]
  ingredientes: Ingredient[]
}

/**
 * PaginatedResponse - API response with pagination metadata
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

/**
 * ProductsApiResponse - Response from GET /api/v1/productos
 */
export type ProductsApiResponse = PaginatedResponse<Product>

/**
 * CategoriesApiResponse - Response from GET /api/v1/categorias
 */
export type CategoriesApiResponse = Category[]

/**
 * CatalogFilters - Current filter state
 */
export interface CatalogFilters {
  categoryIds: string[]
  search: string
  excludeAllergens: string[] // Allergen IDs to exclude
  currentPage: number
}

/**
 * ProductCardProps - Props for ProductCard component
 */
export interface ProductCardProps {
  product: Product
  onViewDetails: (product: Product) => void
  onAddToCart: (product: Product) => void
}

/**
 * ProductDetailProps - Props for ProductDetail modal
 */
export interface ProductDetailProps {
  product: Product
  isOpen: boolean
  onClose: () => void
  onAddToCart: (product: Product, quantity: number) => void
}
