/**
 * StateTransitionModal tests.
 *
 * Covers:
 *   - Renders only valid transitions from FSM_TRANSITIONS
 *   - Terminal state shows message, no radio inputs
 *   - Submit button disabled when no state is selected
 *   - Escape key triggers onClose
 *   - Dialog has correct ARIA attributes
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StateTransitionModal } from '../StateTransitionModal'

// Mock useAdvanceOrderState — avoid real API calls
vi.mock('@/features/orders/hooks/useAdvanceOrderState', () => ({
  useAdvanceOrderState: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}))

// Mock useBulkOrderActions
vi.mock('@/features/orders/hooks/useBulkOrderActions', () => ({
  useBulkOrderActions: () => ({
    bulkAdvanceState: vi.fn(),
    bulkCancel: vi.fn(),
  }),
}))

// Mock useUIStore to avoid localStorage in tests
vi.mock('@/store/uiStore', () => ({
  useUIStore: (selector: (s: { addToast: ReturnType<typeof vi.fn> }) => unknown) =>
    selector({ addToast: vi.fn() }),
}))

function renderModal(props: Partial<Parameters<typeof StateTransitionModal>[0]> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const defaultProps = {
    orderId: 5,
    currentStatusId: 2,
    isOpen: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  }
  return render(
    <QueryClientProvider client={qc}>
      <StateTransitionModal {...defaultProps} {...props} />
    </QueryClientProvider>,
  )
}

describe('StateTransitionModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the modal title when open', () => {
    renderModal()
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('renders valid transitions for estado 2 (CONFIRMADO → EN_PREPARACIÓN, CANCELADO)', () => {
    renderModal({ currentStatusId: 2 })
    // FSM_TRANSITIONS[2] = [3, 6] → "En preparación" and "Cancelado"
    expect(screen.getByRole('radio', { name: /En preparación/i })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Cancelado/i })).toBeInTheDocument()
  })

  it('renders valid transition for estado 3 (EN_PREPARACIÓN → EN_CAMINO)', () => {
    renderModal({ currentStatusId: 3 })
    // FSM_TRANSITIONS[3] = [4] → "En camino"
    expect(screen.getByRole('radio', { name: /En camino/i })).toBeInTheDocument()
  })

  it('shows terminal state message for estado 5 (ENTREGADO)', () => {
    renderModal({ currentStatusId: 5 })
    expect(screen.getByText(/estado terminal/i)).toBeInTheDocument()
    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  })

  it('shows terminal state message for estado 6 (CANCELADO)', () => {
    renderModal({ currentStatusId: 6 })
    expect(screen.getByText(/estado terminal/i)).toBeInTheDocument()
    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  })

  it('confirm button is disabled when no radio is selected', () => {
    renderModal({ currentStatusId: 2 })
    const confirmBtn = screen.getByText('Confirmar cambio')
    expect(confirmBtn).toBeDisabled()
  })

  it('confirm button becomes enabled after selecting a radio', () => {
    renderModal({ currentStatusId: 2 })
    const radio = screen.getByRole('radio', { name: /En preparación/i })
    fireEvent.click(radio)
    const confirmBtn = screen.getByText('Confirmar cambio')
    expect(confirmBtn).not.toBeDisabled()
  })

  it('calls onClose when Escape key is pressed', () => {
    const onClose = vi.fn()
    renderModal({ onClose })
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('has role="dialog" and aria-modal="true"', () => {
    renderModal()
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
  })

  it('does not render anything when isOpen=false', () => {
    renderModal({ isOpen: false })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows orderId in the title', () => {
    renderModal({ orderId: 42 })
    expect(screen.getByText(/pedido #42/i)).toBeInTheDocument()
  })

  it('shows bulk count in title for bulk mode', () => {
    renderModal({
      isBulkMode: true,
      bulkOrderIds: [1, 2, 3],
      currentStatusId: 2,
    })
    expect(screen.getByText(/3 pedidos/i)).toBeInTheDocument()
  })
})
