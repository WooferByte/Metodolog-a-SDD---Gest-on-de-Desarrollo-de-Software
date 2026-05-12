/**
 * Pagination Component
 * 
 * Navigation controls for paginated results:
 * - Page number buttons
 * - Previous/Next buttons
 * - Items count display
 * - Keyboard navigation support
 * 
 * @component
 */

import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  currentPage: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
  isLoading?: boolean
}

/**
 * Pagination Component
 * 
 * @param currentPage - Current page number (1-based)
 * @param totalItems - Total number of items
 * @param itemsPerPage - Items per page
 * @param onPageChange - Callback when page changes
 * @param isLoading - Whether data is loading
 */
export function Pagination({
  currentPage,
  totalItems,
  itemsPerPage,
  onPageChange,
  isLoading = false,
}: PaginationProps) {
  // Calculate pagination values
  const totalPages = Math.ceil(totalItems / itemsPerPage)
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  // Generate page numbers to display (show max 7 pages)
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const maxPages = 7
    const sidePages = 2

    if (totalPages <= maxPages) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // Always show first page
      pages.push(1)

      // Add left dots if needed
      if (currentPage > sidePages + 2) {
        pages.push('...')
      }

      // Add pages around current
      for (let i = Math.max(2, currentPage - sidePages); i <= Math.min(totalPages - 1, currentPage + sidePages); i++) {
        pages.push(i)
      }

      // Add right dots if needed
      if (currentPage < totalPages - sidePages - 1) {
        pages.push('...')
      }

      // Always show last page
      pages.push(totalPages)
    }

    return pages
  }

  const pages = getPageNumbers()

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1)
      // Scroll to top of grid
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1)
      // Scroll to top of grid
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const handlePageClick = (page: number) => {
    if (page !== currentPage) {
      onPageChange(page)
      // Scroll to top of grid
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  if (totalPages <= 1) {
    return null
  }

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-6">
      {/* Items Count Display */}
      <p className="text-sm text-muted-foreground">
        Showing <span className="font-semibold">{startItem}</span> to{' '}
        <span className="font-semibold">{endItem}</span> of{' '}
        <span className="font-semibold">{totalItems}</span> products
      </p>

      {/* Pagination Controls */}
      <nav
        aria-label="Pagination"
        className="flex items-center gap-2 flex-wrap justify-center"
      >
        {/* Previous Button */}
        <button
          onClick={handlePreviousPage}
          disabled={currentPage === 1 || isLoading}
          className="inline-flex items-center gap-1 px-3 py-2 border border-border rounded-lg hover:bg-muted/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Previous page"
          aria-disabled={currentPage === 1}
        >
          <ChevronLeft size={16} />
          <span className="hidden sm:inline">Previous</span>
        </button>

        {/* Page Numbers */}
        <div className="flex gap-1">
          {pages.map((page, index) => (
            page === '...' ? (
              <span key={`dots-${index}`} className="px-2 py-2 text-muted-foreground">
                ...
              </span>
            ) : (
              <button
                key={page}
                onClick={() => handlePageClick(page as number)}
                disabled={page === currentPage || isLoading}
                className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                  page === currentPage
                    ? 'bg-blue-600 text-white'
                    : 'border border-border text-foreground hover:bg-muted/50'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
                aria-label={`Go to page ${page}`}
                aria-current={page === currentPage ? 'page' : undefined}
              >
                {page}
              </button>
            )
          ))}
        </div>

        {/* Next Button */}
        <button
          onClick={handleNextPage}
          disabled={currentPage === totalPages || isLoading}
          className="inline-flex items-center gap-1 px-3 py-2 border border-border rounded-lg hover:bg-muted/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Next page"
          aria-disabled={currentPage === totalPages}
        >
          <span className="hidden sm:inline">Next</span>
          <ChevronRight size={16} />
        </button>
      </nav>

      {/* Page Info */}
      <p className="text-xs text-muted-foreground">
        Page <span className="font-semibold">{currentPage}</span> of{' '}
        <span className="font-semibold">{totalPages}</span>
      </p>
    </div>
  )
}

export type { PaginationProps }
