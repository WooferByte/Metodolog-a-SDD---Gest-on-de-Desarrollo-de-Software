## ADDED Requirements

### Requirement: Display Product Grid

The system SHALL render a responsive grid of product cards on the `/catalog` page.

#### Scenario: Load catalog on desktop
- **WHEN** user navigates to `/catalog` on desktop (1200px+ width)
- **THEN** system displays 4 product cards per row in a grid layout with 1rem gap between cards

#### Scenario: Load catalog on tablet
- **WHEN** user navigates to `/catalog` on tablet (768px width)
- **THEN** system displays 2-3 product cards per row depending on screen size

#### Scenario: Load catalog on mobile
- **WHEN** user navigates to `/catalog` on mobile (< 640px width)
- **THEN** system displays 1 product card per row (full width)

---

### Requirement: ProductCard Component

ProductCard SHALL display a product in thumbnail form with: image, name, price, availability badge, and action buttons.

#### Scenario: Render ProductCard with available product
- **WHEN** ProductCard receives a product with `disponible=true` and `stock_cantidad > 0`
- **THEN** card shows product image, name, price formatted as currency ($XX.XX), green "In Stock" badge, "View Details" button, and "Add to Cart" button

#### Scenario: Render ProductCard with unavailable product
- **WHEN** ProductCard receives a product with `disponible=false` or `stock_cantidad <= 0`
- **THEN** card shows all content as in available case, but with red "Out of Stock" badge and "Add to Cart" button is disabled (grayed out)

#### Scenario: ProductCard image not found
- **WHEN** ProductCard attempts to load an invalid `imagen_url`
- **THEN** card displays a placeholder image (icon) instead and logs warning to console

---

### Requirement: Product Search with Debounce

The system SHALL allow users to search products by name/description with debounced API calls (250ms delay).

#### Scenario: User types search query
- **WHEN** user types in the search input field
- **THEN** system waits 250ms after the last keystroke before calling `GET /api/v1/productos?busqueda=<query>`

#### Scenario: Search clears results
- **WHEN** user clears the search input
- **THEN** system returns to the full product list immediately (no debounce delay)

#### Scenario: Search results empty
- **WHEN** user searches for a term that matches no products
- **THEN** system displays a message "No products found" and provides an option to clear filters

---

### Requirement: Category Filtering

The system SHALL allow users to filter products by category using a multi-select dropdown.

#### Scenario: Category dropdown displays hierarchical categories
- **WHEN** user opens the category filter dropdown
- **THEN** system displays all available categories fetched from `GET /api/v1/categorias` in a tree structure (parent categories and children indented)

#### Scenario: User selects single category
- **WHEN** user clicks on a category name
- **THEN** system filters products to show only those in that category by calling `GET /api/v1/productos?categoria=<id>`

#### Scenario: User selects multiple categories
- **WHEN** user selects 2+ categories
- **THEN** system filters products to show those in ANY of the selected categories (OR logic), passing `?categoria=1,2,3`

#### Scenario: User clears category filter
- **WHEN** user clicks "Clear" or unchecks all categories
- **THEN** system returns to showing all products

---

### Requirement: Allergen Exclusion Filter

The system SHALL allow users to exclude products containing specific allergens.

#### Scenario: User selects allergen to exclude
- **WHEN** user checks a checkbox next to an allergen name (e.g., "peanuts", "dairy")
- **THEN** system filters products by calling `GET /api/v1/productos?excluirAlergenos=<ids>` and displays only products that do NOT contain that allergen

#### Scenario: User excludes multiple allergens
- **WHEN** user checks 2+ allergen checkboxes
- **THEN** system filters products to exclude ANY products that contain ANY of those allergens (AND logic), e.g., `?excluirAlergenos=1,3,5`

#### Scenario: Applied allergen filter shown
- **WHEN** user has active allergen filters
- **THEN** system displays a filter badge showing "Excluding: peanuts, dairy" or similar

---

### Requirement: Pagination

The system SHALL support pagination with 20 products per page and navigation controls.

#### Scenario: Display first page
- **WHEN** user loads the catalog or resets filters
- **THEN** system displays page 1, showing products 1-20 and pagination buttons (1, 2, 3..., Next)

#### Scenario: Navigate to next page
- **WHEN** user clicks "Next" button or page number (e.g., "2")
- **THEN** system calls `GET /api/v1/productos?page=2&limit=20` and displays products 21-40

#### Scenario: Pagination with total count
- **WHEN** system fetches products with pagination
- **THEN** system displays "Showing 1-20 of 150 products" and total page count

#### Scenario: Last page with fewer items
- **WHEN** user navigates to the last page where total products is not a multiple of 20
- **THEN** system shows the remaining products (e.g., 3 products on page 6 if total is 103)

---

### Requirement: ProductDetail Modal

The system SHALL display full product details in a modal dialog when user clicks "View Details" or taps a product card.

#### Scenario: Open ProductDetail modal
- **WHEN** user clicks "View Details" button on ProductCard
- **THEN** system opens a modal displaying: product image, name, description, price, categories (as tags), ingredients (with allergen indicators), and "Add to Cart" button

#### Scenario: ProductDetail modal shows allergen warnings
- **WHEN** ProductDetail modal renders and product contains allergens (is_alergeno=true for any ingredient)
- **THEN** system highlights those ingredients with a red badge or icon and displays "⚠️ Contains common allergens"

#### Scenario: Close ProductDetail modal
- **WHEN** user clicks close button (X), backdrop, or presses Escape key
- **THEN** system closes the modal and returns focus to the grid

#### Scenario: ProductDetail modal is responsive
- **WHEN** user views ProductDetail modal on mobile device
- **THEN** modal displays at full width with vertical scrolling if content exceeds screen height

---

### Requirement: Add to Cart from Catalog

The system SHALL allow users to add products to the cart from ProductCard or ProductDetail with quantity selection.

#### Scenario: Add to cart from ProductCard
- **WHEN** user clicks "Add to Cart" button on ProductCard
- **THEN** system opens a mini quantity selector (qty: 1 with +/- buttons) and "Add" button, or adds 1 item to cart directly if configured for quick add

#### Scenario: Add to cart from ProductDetail modal
- **WHEN** user selects quantity in ProductDetail modal and clicks "Add to Cart"
- **THEN** system adds that quantity to cartStore (Zustand), closes modal, and shows a success toast notification "Added to cart!"

#### Scenario: Cart updates immediately
- **WHEN** user adds a product to cart
- **THEN** cart icon in navbar updates showing new total item count within 100ms

#### Scenario: Add product already in cart
- **WHEN** user adds a product that already exists in cart
- **THEN** system increments the quantity in cartStore instead of creating a duplicate entry

---

### Requirement: Skeleton Loaders

The system SHALL display skeleton/placeholder loaders while product data is loading.

#### Scenario: Show skeletons on initial load
- **WHEN** user navigates to `/catalog` page
- **THEN** system displays 20 skeleton ProductCard placeholders in grid layout until API response arrives

#### Scenario: Hide skeletons when data loads
- **WHEN** API call completes and products arrive
- **THEN** system replaces skeleton loaders with actual product cards

#### Scenario: Skeleton appears on filter change
- **WHEN** user changes category/search/allergen filters
- **THEN** system shows skeleton loaders again while fetching filtered results

---

### Requirement: Error Handling

The system SHALL handle API errors gracefully with user-friendly messages.

#### Scenario: API timeout or 5xx error
- **WHEN** API call fails or times out after 5 seconds
- **THEN** system displays error message "Failed to load products. Please try again." with a "Retry" button

#### Scenario: No internet connection
- **WHEN** user attempts catalog request with no network connection
- **THEN** system displays "No internet connection" message and allows retry when connection is restored

#### Scenario: Retry successful
- **WHEN** user clicks "Retry" button after error
- **THEN** system retries the API call and displays products if successful

---

### Requirement: Accessibility

The system SHALL meet WCAG 2.1 Level AA accessibility standards.

#### Scenario: ProductCard has alt text
- **WHEN** ProductCard renders a product image
- **THEN** image element has alt attribute describing the product (e.g., "Margherita Pizza")

#### Scenario: Search input is labeled
- **WHEN** search input field is rendered
- **THEN** input has associated label element and aria-label for screen readers

#### Scenario: Keyboard navigation
- **WHEN** user navigates using keyboard (Tab key) on the catalog page
- **THEN** all interactive elements (buttons, dropdowns, inputs) are reachable and in logical order

#### Scenario: Modal has focus trap
- **WHEN** ProductDetail modal is open
- **THEN** Tab key cycles through modal content only; closing modal returns focus to triggering element

---

### Requirement: Performance

The system SHALL meet performance targets for catalog page load and interaction.

#### Scenario: Catalog page loads within 2 seconds
- **WHEN** user navigates to `/catalog` on first visit
- **THEN** page is interactive (can click buttons) within 2 seconds on 4G connection

#### Scenario: Filter response within 500ms
- **WHEN** user changes category/search filter
- **THEN** filtered results appear within 500ms (excluding skeleton loading time)

#### Scenario: Image lazy loading
- **WHEN** ProductCard renders
- **THEN** product images are lazy-loaded (loading="lazy" attribute), not all loaded on page entry

---

### Requirement: Filter UI State

The system SHALL display active filters and provide easy clearing.

#### Scenario: Display applied filters
- **WHEN** user has active filters (category, search, allergens)
- **THEN** system displays a "Applied Filters" summary showing all active filters as removable tags

#### Scenario: Clear individual filter
- **WHEN** user clicks X button on a filter tag
- **THEN** system removes that filter and refreshes results immediately

#### Scenario: Clear all filters
- **WHEN** user clicks "Clear All" button
- **THEN** system resets all filters to default and displays full product list
