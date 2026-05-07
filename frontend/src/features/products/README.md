# Product Catalog Feature

Complete product catalog UI for FoodStore with search, filtering, pagination, and cart integration.

## Overview

The product catalog provides a public-facing interface for customers to:
- Browse all available products in a responsive grid
- Search products by name/description (debounced)
- Filter by category (multi-select, hierarchical)
- Exclude products containing specific allergens
- View full product details in a modal
- Add items to cart with quantity selection

## Architecture

### Folder Structure

```
frontend/src/features/products/
├── types/
│   └── index.ts              # Type definitions
├── constants/
│   └── index.ts              # Constants (pagination, debounce, etc.)
├── hooks/
│   ├── useProductsCatalog.ts # Main API hook for paginated products
│   ├── useProductDetail.ts   # Single product detail hook
│   ├── useCategoriesHierarchy.ts # Categories hook with hierarchy builder
│   ├── useAllergensFilter.ts # Allergen extraction hook
│   └── index.ts              # Barrel exports
├── components/
│   ├── ProductCard.tsx       # Product thumbnail component
│   ├── ProductDetail.tsx     # Full-screen modal with details
│   ├── ProductGrid.tsx       # Responsive grid layout with skeletons
│   ├── SearchInput.tsx       # Debounced search input
│   ├── CategoryFilter.tsx    # Multi-select category dropdown
│   ├── AllergenFilter.tsx    # Allergen exclusion checkboxes
│   ├── AppliedFilters.tsx    # Display active filters as tags
│   ├── Pagination.tsx        # Page navigation controls
│   ├── FilterBar.tsx         # Main filter sidebar
│   └── index.ts              # Component barrel exports
└── README.md                 # This file
```

### Component Hierarchy

```
CatalogPage (src/pages/Catalog.tsx)
├── FilterBar
│   ├── SearchInput
│   ├── CategoryFilter
│   └── AllergenFilter
├── AppliedFilters
├── ProductGrid
│   ├── ProductCard (multiple)
│   ├── SkeletonCard (during loading)
│   └── Error UI (on failure)
├── Pagination
└── ProductDetail (modal)
```

## Key Components

### ProductCard (`ProductCard.tsx`)

Displays product in thumbnail form.

**Features:**
- Lazy-loaded images with fallback placeholder
- In Stock / Out of Stock badge
- Allergen warning indicator (⚠️)
- "View Details" and "Add to Cart" buttons
- Disabled Add to Cart when unavailable

**Props:**
```typescript
{
  product: Product
  onViewDetails: (product: Product) => void
  onAddToCart: (product: Product) => void
}
```

### ProductDetail (`ProductDetail.tsx`)

Full-screen modal for product details.

**Features:**
- Modal with backdrop and close button
- Escape key to close
- Focus trap (Tab cycles within modal)
- Product image, name, description, categories
- Ingredients list with allergen indicators (🔴)
- Allergen warning banner when applicable
- Quantity selector with +/- buttons
- Add to Cart button with quantity selection
- Responsive (full-width on mobile, centered on desktop)

**Props:**
```typescript
{
  product: Product | null
  isOpen: boolean
  onClose: () => void
  onAddToCart: (product: Product, quantity: number) => void
}
```

### ProductGrid (`ProductGrid.tsx`)

Responsive grid container for products.

**Features:**
- Responsive columns: 1 (mobile), 2 (tablet), 3-4 (desktop)
- Skeleton loaders (20 items) while loading
- "No products found" message when empty
- Error state with retry button
- Loading state handling

**Props:**
```typescript
{
  products: Product[] | undefined
  isLoading: boolean
  isError: boolean
  error?: Error | null
  onRetry?: () => void
  onViewDetails: (product: Product) => void
  onAddToCart: (product: Product) => void
}
```

### SearchInput (`SearchInput.tsx`)

Debounced search input.

**Features:**
- 250ms debounce delay to prevent excessive API calls
- Clear button (X) when text entered
- Search icon indicator
- Accessible labeling

**Props:**
```typescript
{
  value: string
  onChange: (value: string) => void
  placeholder?: string
}
```

### CategoryFilter (`CategoryFilter.tsx`)

Multi-select category filter with hierarchy support.

**Features:**
- Desktop: Always visible checkbox list (scrollable)
- Mobile: Collapsible dropdown
- Hierarchical categories (parent/child indentation)
- Clear All button
- Max height with scroll on desktop

**Props:**
```typescript
{
  selectedIds: string[]
  onChange: (ids: string[]) => void
}
```

### AllergenFilter (`AllergenFilter.tsx`)

Allergen exclusion checkboxes.

**Features:**
- Displays all allergens found in current products
- Shows product count per allergen
- Sorted by frequency (most common first)
- Scrollable list with max height
- Clear All button

**Props:**
```typescript
{
  allergens: AllergenItem[]
  selectedIds: string[]
  onChange: (ids: string[]) => void
  isLoading?: boolean
}
```

### Pagination (`Pagination.tsx`)

Page navigation with information display.

**Features:**
- Shows "Showing X-Y of Z products" text
- Page number buttons with smart truncation (max 7 pages shown)
- Previous/Next buttons
- Current page indicator
- Disabled state when at first/last page
- Smooth scroll to top on page change
- Keyboard navigation support

**Props:**
```typescript
{
  currentPage: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
  isLoading?: boolean
}
```

## Hooks (API Integration)

All hooks use **React Query** (TanStack Query) for:
- Automatic caching with stale-while-revalidate strategy
- Retry logic on failures
- Error handling and loading states

### useProductsCatalog

Main hook for fetching paginated products with filters.

```typescript
const { data, isPending, isError, error, refetch } = useProductsCatalog(
  {
    categoryIds: ['1', '2'],
    search: 'pizza',
    excludeAllergens: ['3'],
    currentPage: 1
  },
  20 // items per page
)

// Returns:
// data: { items: Product[], total: number, page: number, limit: number }
```

**Query Key Pattern:**
```typescript
[QUERY_KEYS.PRODUCTS, filters] // Re-fetches when filters change
```

**Caching:**
- Stale time: 5 minutes
- GC time: 10 minutes

**Retry Strategy:**
- 2 retries for 5xx errors or network failures
- Exponential backoff: 1s, 2s, 4s (max 30s)
- No retry for 4xx errors (except 408 timeout)

### useProductDetail

Fetches single product details.

```typescript
const { data: product, isPending, isError } = useProductDetail(productId)
```

**Features:**
- Disabled if no productId
- Long cache (10 min stale, 30 min GC)
- Minimal retry (1 attempt)

### useCategoriesHierarchy

Fetches and provides utility to build category tree.

```typescript
const { data: categories } = useCategoriesHierarchy()
const hierarchy = buildCategoryHierarchy(categories)

// hierarchy.parents - Top-level categories
// hierarchy.children - Subcategories
// hierarchy.getChildren(parentId) - Get children of specific parent
```

### useAllergensFilter

Extracts unique allergens from products list with counts.

```typescript
const allergens = useAllergensFilter(products)

// Returns: Array<{ id: string, nombre: string, count: number }>
// Sorted by frequency (most common first)
```

## State Management

### Local Component State (React Hooks)

CatalogPage manages:
- Filter state: `{ categoryIds, search, excludeAllergens, currentPage }`
- Modal state: `{ selectedProduct, isDetailOpen }`

Rationale: Filters are ephemeral UI state, not persistent across sessions.

### Global State (Zustand Stores)

**cartStore** (shopping cart):
- `addItem(item)` - Add or increment product quantity
- `items` - Array of cart items
- `totalPrice()` - Compute total

**uiStore** (UI notifications):
- `addToast(message, type, duration)` - Show success/error messages

## API Integration

### Endpoints

| Method | Path | Query Params | Response |
|--------|------|--------------|----------|
| GET | `/api/v1/productos` | `?categoria=id&busqueda=term&excluirAlergenos=1,3&page=1&limit=20` | `{ items: Product[], total: number, page: number, limit: number }` |
| GET | `/api/v1/productos/:id` | - | `Product` |
| GET | `/api/v1/categorias` | - | `Category[]` |

### Error Handling

| Error | UI Response | Retry? |
|-------|-------------|--------|
| Network timeout (5s) | "Failed to load products. Please try again." with Retry button | Yes, 2 attempts |
| 5xx Server error | Same as timeout | Yes, exponential backoff |
| 4xx Client error | Error message from API | No |
| No internet | "No internet connection" | Retry on connection restore |
| Empty results | "No products found" | N/A (not an error) |

## Performance Optimizations

1. **Image Lazy Loading**
   - `loading="lazy"` attribute on product images
   - Images only load when entering viewport

2. **API Caching**
   - React Query caches results by filter state
   - Returning to previous page/filters uses cache
   - No redundant API calls for same data

3. **Debounced Search**
   - 250ms delay prevents API call spam while typing
   - Clear search triggers immediately (no debounce)

4. **Pagination**
   - 20 items per page (configurable)
   - Prevents loading 100+ products at once
   - Improves initial load time

5. **Skeleton Loaders**
   - Show while fetching (better perceived performance)
   - Match final card dimensions

6. **Memoization**
   - `useAllergensFilter` uses `useMemo` to prevent recalculations
   - `AppliedFilters` component memoizes allergen map

## Accessibility (WCAG 2.1 AA)

### Implemented

✅ Alt text on all product images
✅ Semantic HTML (fieldset, legend, buttons, inputs)
✅ ARIA labels on all inputs and buttons
✅ Keyboard navigation (Tab through all controls)
✅ Focus management in modals (focus trap, restore focus on close)
✅ Color contrast (minimum 4.5:1 for text)
✅ Modal close on Escape key
✅ Screen reader announcements (role, aria-label, aria-current)
✅ Loading states with spinner (accessible)
✅ Error messages in focus area

### Testing

Test with:
- **Narrator** (Windows): `Win + Ctrl + N`
- **NVDA** (Windows): Free screen reader
- **VoiceOver** (Mac): `Cmd + F5`
- **JAWS** (expensive, common in enterprises)

Tab through controls manually to verify order.

## Responsive Design

### Breakpoints

| Device | Width | Grid Cols | Layout |
|--------|-------|-----------|--------|
| Mobile | < 640px | 1 | Full-width cards, filter hamburger |
| Tablet | 640-1024px | 2-3 | 2-3 columns, sidebar visible |
| Desktop | 1024px+ | 3-4 | 3-4 columns, full sidebar |

### Testing

Test at actual device sizes:
- **Mobile**: 375px (iPhone SE), 414px (iPhone 12)
- **Tablet**: 768px (iPad), 1024px (iPad Pro)
- **Desktop**: 1280px, 1440px, 1920px

Use DevTools device emulation:
- Chrome: F12 → Device toolbar (Ctrl+Shift+M)
- Firefox: F12 → Responsive Design Mode (Ctrl+Shift+M)

## Constants

```typescript
ITEMS_PER_PAGE = 20                    // Products per page
SEARCH_DEBOUNCE_DELAY = 250            // Search input debounce (ms)
API_TIMEOUT = 5000                     // API request timeout (ms)
MAX_QUANTITY = 999                     // Max items per cart item
MIN_QUANTITY = 1                       // Min items per cart item
TOAST_DURATION = 3000                  // Toast notification duration (ms)
```

## Usage Example

```tsx
import CatalogPage from '@/pages/Catalog'

export default function App() {
  return (
    <Routes>
      <Route path="/catalog" element={<CatalogPage />} />
      <Route path="/" element={<CatalogPage />} />
    </Routes>
  )
}
```

## Testing Checklist

### Manual Testing

- [ ] Products load on page entry
- [ ] Search works (debounce visible in Network tab)
- [ ] Category filter updates products
- [ ] Allergen filter excludes products
- [ ] Pagination navigates correctly
- [ ] View Details opens modal
- [ ] Modal closes on Escape, backdrop click, or X button
- [ ] Quantity selector +/- buttons work
- [ ] Add to Cart updates cart icon
- [ ] Add to Cart shows success toast
- [ ] Error handling works (disconnect API, see error message + retry)

### Responsive Testing

- [ ] Mobile (375px): Cards stack 1 per row, filter hamburger works
- [ ] Tablet (768px): Cards show 2-3 per row
- [ ] Desktop (1200px+): Cards show 3-4 per row, sidebar always visible

### Accessibility Testing

- [ ] All images have alt text
- [ ] Can navigate entire page with Tab key
- [ ] Modal focus trap works (Tab within modal only)
- [ ] Screen reader announces product names
- [ ] Applied filters display and update
- [ ] Error messages are announced

### Performance Testing

- [ ] Initial load < 2 seconds
- [ ] Filter response < 500ms
- [ ] Images lazy load (not all load on page entry)
- [ ] No console errors or warnings

## Troubleshooting

### Products not loading

1. Check API is running (`http://localhost:8000/api/v1/productos`)
2. Check Network tab for 5xx errors
3. Check browser console for error messages
4. Verify VITE_API_BASE_URL environment variable is set

### Modal not closing

1. Check browser console for errors
2. Verify Escape key listener is attached
3. Check modal `zIndex` is not overlapped

### Search not updating

1. Verify debounce delay (250ms) in Network tab
2. Check search term is being sent in query params
3. Verify API supports `?busqueda=` parameter

### Filters not working

1. Check category IDs in query params
2. Verify category filter is sending correct IDs
3. Check allergen IDs are being sent as comma-separated

## Future Enhancements

1. **URL Query Params**: Store filters in URL for shareable links
2. **Wishlist**: Add products to wishlist (requires backend API)
3. **Product Reviews**: Display ratings and reviews
4. **Advanced Filters**: Price range, nutritional info
5. **Infinite Scroll**: Replace pagination with scroll-based loading
6. **Search Analytics**: Track popular searches
7. **Product Recommendations**: "You might also like..."
8. **Inventory Alerts**: Notify when out-of-stock product is back

## References

- [Tailwind CSS v4 Docs](https://tailwindcss.com/docs)
- [React Query Docs](https://tanstack.com/query/latest)
- [Zustand Docs](https://github.com/pmndrs/zustand)
- [Lucide React Icons](https://lucide.dev/)
- [WCAG 2.1 Standards](https://www.w3.org/WAI/WCAG21/quickref/)
