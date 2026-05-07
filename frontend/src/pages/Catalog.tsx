/**
 * Catalog Page Component
 * 
 * Main page for the product catalog with:
 * - Filter bar (search, categories, allergens)
 * - Product grid with responsive layout
 * - Product detail modal
 * - Pagination
 * - Integrated cart management
 * 
 * Architecture:
 * - Container component (handles state, API calls)
 * - Presenter component (renders UI)
 * 
 * @component
 */

import { useState, useMemo } from 'react'
import { useCartStore } from '@/store/cartStore'
import { useUIStore } from '@/store/uiStore'
import {
  useProductsCatalog,
  useAllergensFilter,
} from '@/features/products/hooks'
import {
  ProductGrid,
  ProductDetail,
  FilterBar,
  Pagination,
  AppliedFilters,
} from '@/features/products/components'
import { ITEMS_PER_PAGE } from '@/features/products/constants'
import type { Product, CatalogFilters } from '@/features/products/types'

/**
 * CatalogPage Component
 * 
 * Main catalog page that orchestrates:
 * - Filter state management
 * - API calls via React Query
 * - Cart integration with Zustand
 * - Modal state management
 */
export default function CatalogPage() {
  // Filter state
  const [filters, setFilters] = useState<CatalogFilters>({
    categoryIds: [],
    search: '',
    excludeAllergens: [],
    currentPage: 1,
  })

  // Modal state
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)

  // Store access
  const addToCart = useCartStore((state) => state.addItem)
  const addToast = useUIStore((state) => state.addToast)

  // Fetch products with current filters
  const { data: catalogData, isPending, isError, error, refetch } = useProductsCatalog(
    filters,
    ITEMS_PER_PAGE,
  )

  // Extract allergens from current products for display
  const allergens = useAllergensFilter(catalogData?.items)

  // Memoize allergen map for AppliedFilters component
  const allergenMap = useMemo(
    () => allergens.map((a) => ({ id: a.id, nombre: a.nombre })),
    [allergens],
  )

  // ===== Filter Handlers =====

  const handleSearchChange = (search: string) => {
    setFilters((prev) => ({
      ...prev,
      search,
      currentPage: 1, // Reset to page 1 when search changes
    }))
  }

  const handleCategoryChange = (categoryIds: string[]) => {
    setFilters((prev) => ({
      ...prev,
      categoryIds,
      currentPage: 1, // Reset to page 1 when filter changes
    }))
  }

  const handleAllergenChange = (excludeAllergens: string[]) => {
    setFilters((prev) => ({
      ...prev,
      excludeAllergens,
      currentPage: 1, // Reset to page 1 when filter changes
    }))
  }

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({
      ...prev,
      currentPage: page,
    }))
  }

  // ===== Filter Manipulation Handlers =====

  const handleRemoveCategory = (categoryId: string) => {
    handleCategoryChange(filters.categoryIds.filter((id) => id !== categoryId))
  }

  const handleRemoveAllergen = (allergenId: string) => {
    handleAllergenChange(filters.excludeAllergens.filter((id) => id !== allergenId))
  }

  const handleClearSearch = () => {
    handleSearchChange('')
  }

  const handleClearAllFilters = () => {
    setFilters({
      categoryIds: [],
      search: '',
      excludeAllergens: [],
      currentPage: 1,
    })
  }

  // ===== Modal Handlers =====

  const handleViewDetails = (product: Product) => {
    setSelectedProduct(product)
    setIsDetailOpen(true)
  }

  const handleCloseDetail = () => {
    setIsDetailOpen(false)
    setSelectedProduct(null)
  }

  // ===== Cart Integration =====

  const handleAddToCart = (product: Product, quantity: number) => {
    try {
      addToCart({
        productId: product.id,
        name: product.nombre,
        price: product.precio,
        quantity,
        image: product.imagen_url,
      })

      // Show success toast
      addToast({
        message: `Added ${quantity}x ${product.nombre} to cart!`,
        type: 'success',
        duration: 2000,
      })

      // Close modal
      handleCloseDetail()
    } catch (err) {
      addToast({
        message: 'Failed to add item to cart. Please try again.',
        type: 'error',
        duration: 3000,
      })
    }
  }

  const handleAddToCartFromCard = (product: Product) => {
    // Quick add with quantity 1
    handleAddToCart(product, 1)
  }

  // ===== Render =====

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Product Catalog
          </h1>
          <p className="text-gray-600">
            Browse our selection of delicious products
          </p>
        </div>

        {/* Applied Filters Summary */}
        <AppliedFilters
          search={filters.search}
          categoryIds={filters.categoryIds}
          excludeAllergens={filters.excludeAllergens}
          allergens={allergenMap}
          onRemoveCategory={handleRemoveCategory}
          onRemoveAllergen={handleRemoveAllergen}
          onClearSearch={handleClearSearch}
          onClearAll={handleClearAllFilters}
        />

        {/* Main Content: Filters + Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          {/* Filter Sidebar */}
          <div className="md:col-span-1">
            <FilterBar
              search={filters.search}
              categoryIds={filters.categoryIds}
              excludeAllergens={filters.excludeAllergens}
              products={catalogData?.items}
              onSearchChange={handleSearchChange}
              onCategoryChange={handleCategoryChange}
              onAllergenChange={handleAllergenChange}
            />
          </div>

          {/* Products Grid */}
          <div className="md:col-span-3">
            <ProductGrid
              products={catalogData?.items}
              isLoading={isPending}
              isError={isError}
              error={error}
              onRetry={refetch}
              onViewDetails={handleViewDetails}
              onAddToCart={handleAddToCartFromCard}
            />
          </div>
        </div>

        {/* Pagination */}
        {catalogData && !isError && (
          <Pagination
            currentPage={filters.currentPage}
            totalItems={catalogData.total}
            itemsPerPage={ITEMS_PER_PAGE}
            onPageChange={handlePageChange}
            isLoading={isPending}
          />
        )}
      </div>

      {/* Product Detail Modal */}
      <ProductDetail
        product={selectedProduct}
        isOpen={isDetailOpen}
        onClose={handleCloseDetail}
        onAddToCart={handleAddToCart}
      />
    </div>
  )
}
