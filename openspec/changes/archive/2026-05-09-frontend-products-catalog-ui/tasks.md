## 1. Project Setup & Folder Structure

- [x] 1.1 Create folder structure: `frontend/src/features/products/components/` and `frontend/src/features/products/hooks/`
- [x] 1.2 Create folder structure: `frontend/src/pages/CatalogPage.tsx`
- [x] 1.3 Create `frontend/src/features/products/types/index.ts` with ProductCard, ProductDetail, CatalogFilter types
- [x] 1.4 Create `frontend/src/features/products/constants/index.ts` with constants (ITEMS_PER_PAGE=20, DEBOUNCE_DELAY=250, etc.)

## 2. API Integration & Hooks

- [x] 2.1 Create hook `frontend/src/features/products/hooks/useProductsCatalog.ts` that uses React Query to fetch products with filters (category, search, allergen, pagination)
- [x] 2.2 Create hook `frontend/src/features/products/hooks/useProductDetail.ts` for fetching single product details
- [x] 2.3 Create hook `frontend/src/features/products/hooks/useCategoriesHierarchy.ts` for fetching categories from API
- [x] 2.4 Create hook `frontend/src/features/products/hooks/useAllergensFilter.ts` for fetching unique allergen list from products
- [x] 2.5 Add type definitions for API responses (Product, Category, Ingredient with allergen flag)

## 3. ProductCard Component

- [x] 3.1 Create component `frontend/src/features/products/components/ProductCard.tsx` with props: product, onViewDetails, onAddToCart
- [x] 3.2 Implement ProductCard UI: image, name, price, availability badge (In Stock / Out of Stock)
- [x] 3.3 Add "View Details" button and "Add to Cart" button to ProductCard
- [x] 3.4 Add image fallback/placeholder when image_url is invalid or missing
- [x] 3.5 Disable "Add to Cart" button when product is unavailable (disponible=false)
- [x] 3.6 Add alt text to product image for accessibility
- [x] 3.7 Style ProductCard with Tailwind CSS (responsive, hover effects)

## 4. ProductDetail Modal Component

- [x] 4.1 Create component `frontend/src/features/products/components/ProductDetail.tsx` (modal) with product data
- [x] 4.2 Implement modal structure: close button (X), product image, name, description, price, categories (as tags), ingredients list
- [x] 4.3 Add allergen indicators (🔴 badge or ⚠️ icon) for ingredients with is_alergeno=true
- [x] 4.4 Add "⚠️ Contains allergens" warning message when product has allergen ingredients
- [x] 4.5 Implement quantity selector (+/- buttons, input field) in modal
- [x] 4.6 Add "Add to Cart" button that triggers cartStore.addItem() with quantity
- [x] 4.7 Implement modal close on Escape key, backdrop click, or X button
- [x] 4.8 Make modal responsive (full-width on mobile, centered on desktop)
- [x] 4.9 Implement focus trap (Tab key cycles within modal) and restore focus on close
- [x] 4.10 Style modal with Tailwind CSS

## 5. Filter Components

- [x] 5.1 Create component `frontend/src/features/products/components/FilterBar.tsx` (sidebar on desktop, collapsible on mobile)
- [x] 5.2 Implement search input with debounced onChange handler (250ms delay)
- [x] 5.3 Create component `frontend/src/features/products/components/CategoryFilter.tsx` (multi-select dropdown with hierarchical categories)
- [x] 5.4 Create component `frontend/src/features/products/components/AllergenFilter.tsx` (checkboxes for allergen exclusion)
- [x] 5.5 Create component `frontend/src/features/products/components/AppliedFilters.tsx` (display active filters as removable tags)
- [x] 5.6 Implement "Clear All" button in FilterBar
- [x] 5.7 Add aria-labels and semantic HTML to all filter inputs
- [x] 5.8 Style filter components with Tailwind CSS (responsive sidebar)

## 6. ProductGrid Component

- [x] 6.1 Create component `frontend/src/features/products/components/ProductGrid.tsx` that renders array of ProductCards in responsive grid
- [x] 6.2 Implement responsive grid layout: 1 col (mobile), 2 cols (tablet), 3-4 cols (desktop) using Tailwind grid classes
- [x] 6.3 Add skeleton loaders (20 items) while data is loading
- [x] 6.4 Display "No products found" message when results are empty
- [x] 6.5 Implement error UI with "Failed to load products" message and Retry button

## 7. Pagination Component

- [x] 7.1 Create component `frontend/src/features/products/components/Pagination.tsx` with page buttons and Next/Previous
- [x] 7.2 Implement pagination logic: calculate total pages, show current page indicator
- [x] 7.3 Display "Showing X-Y of Z products" text
- [x] 7.4 Add keyboard navigation for pagination buttons
- [x] 7.5 Style pagination with Tailwind CSS

## 8. CatalogPage Integration

- [x] 8.1 Create page `frontend/src/pages/CatalogPage.tsx` that composes all components (FilterBar, ProductGrid, Pagination)
- [x] 8.2 Implement local state for filters: { categoryIds, search, excludeAllergens, currentPage }
- [x] 8.3 Implement state handlers: onSearchChange, onCategoryChange, onAllergenChange, onPageChange
- [x] 8.4 Connect state to useProductsCatalog hook
- [x] 8.5 Implement modal state: showDetail, selectedProduct
- [x] 8.6 Pass handlers to ProductCard (onViewDetails → setSelectedProduct, onAddToCart)
- [x] 8.7 Pass handlers to ProductDetail (onClose, onAddToCart → cartStore.addItem())
- [x] 8.8 Add breadcrumb or page title "Catalog" in header

## 9. Shopping Cart Integration

- [x] 9.1 Import cartStore from Zustand store
- [x] 9.2 Call cartStore.addItem(product, quantity) when user clicks "Add to Cart" in ProductDetail
- [x] 9.3 Show success toast notification "Added to cart!" after adding
- [x] 9.4 Handle error if add-to-cart fails (e.g., quantity exceeds stock) with error toast
- [ ] 9.5 Update cart icon/counter in Navbar automatically via cartStore subscription

## 10. Lazy Loading & Performance

- [x] 10.1 Add loading="lazy" attribute to product images for lazy loading
- [ ] 10.2 Implement Intersection Observer for image preloading on ProductCard hover (optional optimization)
- [x] 10.3 Use React Query caching to prevent redundant API calls when returning to catalog
- [ ] 10.4 Test Largest Contentful Paint (LCP) and ensure < 2s load time

## 11. Accessibility & Testing

- [x] 11.1 Add alt text to all product images
- [x] 11.2 Add aria-labels to search, category dropdown, allergen checkboxes
- [ ] 11.3 Verify keyboard navigation (Tab through all controls in logical order)
- [ ] 11.4 Test screen reader compatibility with Narrator (Windows) or VoiceOver (Mac)
- [ ] 11.5 Verify color contrast meets WCAG AA standards (4.5:1 for text)
- [x] 11.6 Test modal focus trap (Tab cycles within modal, not to background)
- [x] 11.7 Test modal close on Escape key

## 12. Routing & Navigation

- [x] 12.1 Add route `/catalog` to React Router (public route, no auth required)
- [ ] 12.2 Add "Catalog" link to navigation menu (Navbar/Sidebar) for all users
- [x] 12.3 Verify route is accessible to unauthenticated users
- [ ] 12.4 Add page title/meta for SEO (use React Helmet or similar if needed)

## 13. Error Handling & Edge Cases

- [x] 13.1 Handle API timeout (5s) with error message and retry
- [x] 13.2 Handle network error with offline message
- [x] 13.3 Handle empty search results with "No products found" UI
- [x] 13.4 Handle pagination edge case (last page with fewer items)
- [x] 13.5 Handle product with no image (display placeholder)
- [x] 13.6 Handle product with no ingredients (show empty list)
- [x] 13.7 Handle concurrent filter changes (debounce + cancel previous request)

## 14. Responsive Design Testing

- [ ] 14.1 Test catalog on mobile device (375px width) — 1 col grid, collapsible filters
- [ ] 14.2 Test catalog on tablet (768px width) — 2-3 col grid
- [ ] 14.3 Test catalog on desktop (1200px+ width) — 4 col grid
- [ ] 14.4 Test ProductDetail modal on mobile (full-width, scrollable)
- [ ] 14.5 Test FilterBar collapse/expand on mobile
- [ ] 14.6 Verify touch events work (tap filters, scroll grid on mobile)

## 15. Documentation & Code Quality

- [x] 15.1 Add JSDoc comments to all hooks and components
- [x] 15.2 Add usage examples for ProductCard, ProductDetail in component files
- [ ] 15.3 Create README.md in `frontend/src/features/products/` documenting component API
- [x] 15.4 Ensure TypeScript strict mode compliance (no any types)
- [ ] 15.5 Run ESLint and fix any issues
- [ ] 15.6 Run Prettier and format all files

## 16. Integration & Verification

- [ ] 16.1 Run `npm run dev` and verify catalog page loads without errors
- [ ] 16.2 Verify API calls in DevTools Network tab (check request/response)
- [ ] 16.3 Verify Zustand store updates in React DevTools when adding to cart
- [ ] 16.4 Verify filters update results correctly (category, search, allergens)
- [ ] 16.5 Verify pagination works (navigate pages, show correct item ranges)
- [ ] 16.6 Verify skeleton loaders appear during loading
- [ ] 16.7 Test "Add to Cart" flow: click button → modal → select qty → add → toast → cart updates
- [ ] 16.8 Verify error handling (disconnect API, test error messages and retry)

## 17. Final Testing & Archive Preparation

- [ ] 17.1 Run all unit tests (if any exist) and ensure they pass
- [ ] 17.2 Perform end-to-end testing on multiple browsers (Chrome, Firefox, Safari)
- [ ] 17.3 Test on real mobile devices (iPhone, Android)
- [ ] 17.4 Document any known issues or limitations
- [ ] 17.5 Create git commit with all changes
- [ ] 17.6 Verify all tasks are marked complete
- [ ] 17.7 Ready for archive phase
