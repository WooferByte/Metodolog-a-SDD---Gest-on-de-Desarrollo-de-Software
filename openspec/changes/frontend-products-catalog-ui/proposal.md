## Why

The FoodStore frontend needs a public-facing product catalog interface that allows customers to browse, search, and filter available products before adding them to the cart. This UI builds on the backend `products-catalog-public` API (already implemented) and the Zustand cart store (CHANGE 7, already completed).

## What Changes

- Introduces a new **Catalog page** (`/catalog`) with grid layout displaying all available products
- Implements **ProductCard component** with product image, name, price, availability status, and "Add to Cart" button
- Implements **ProductDetail modal** for viewing full product details (name, description, price, categories, ingredients with allergen indicators)
- Adds **filter bar** with:
  - Category multi-select dropdown
  - Real-time search with debounce
  - Allergen exclusion checkboxes (to filter out products containing specific allergens)
- Implements **pagination** (20 items per page, with page indicators)
- Adds **skeleton loaders** for product cards while data is loading
- Integrates with **cartStore** (Zustand) to allow "Add to Cart" with quantity selection
- Styling uses **Tailwind CSS v4** with responsive mobile-first design

## Capabilities

### New Capabilities

- `products-catalog-ui`: Frontend page and components for displaying, searching, filtering, and interacting with the product catalog. Supports pagination, category filtering, allergen exclusion, and cart integration.

### Modified Capabilities

- `ui-navigation`: Layout/navigation must include a navigation link to the Catalog page (for non-authenticated users and all roles)

## Impact

- **Frontend files**: New pages and components in `frontend/src/pages/` and `frontend/src/features/products/`
- **Dependencies**: Uses react-query (already installed via CHANGE 5), Zustand (cartStore from CHANGE 8), Tailwind CSS (CHANGE 5), lucide-react icons
- **APIs consumed**: `GET /api/v1/productos` (with category, search, allergen filters, pagination)
- **Breaking changes**: None
