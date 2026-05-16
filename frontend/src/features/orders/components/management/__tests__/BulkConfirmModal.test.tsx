/**
 * BulkConfirmModal tests.
 *
 * Covers:
 *   - Does not render when isOpen=false
 *   - Renders title and message when open
 *   - Confirm button calls onConfirm
 *   - Cancel button calls onClose
 *   - Escape key triggers onClose
 *   - role="alertdialog" and aria-modal are set
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BulkConfirmModal } from '../BulkConfirmModal'

function renderModal(overrides: Partial<Parameters<typeof BulkConfirmModal>[0]> = {}) {
  const defaults = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    title: 'Eliminar pedidos',
    message: '¿Seguro que querés eliminar 3 pedidos?',
    confirmLabel: 'Eliminar 3 pedidos',
    isPending: false,
  }
  return render(<BulkConfirmModal {...defaults} {...overrides} />)
}

describe('BulkConfirmModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does not render when isOpen=false', () => {
    renderModal({ isOpen: false })
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })

  it('renders dialog with role="alertdialog" when open', () => {
    renderModal()
    expect(screen.getByRole('alertdialog')).toBeInTheDocument()
  })

  it('has aria-modal="true"', () => {
    renderModal()
    expect(screen.getByRole('alertdialog')).toHaveAttribute('aria-modal', 'true')
  })

  it('renders title', () => {
    renderModal()
    expect(screen.getByText('Eliminar pedidos')).toBeInTheDocument()
  })

  it('renders message', () => {
    renderModal()
    expect(screen.getByText('¿Seguro que querés eliminar 3 pedidos?')).toBeInTheDocument()
  })

  it('clicking Confirmar button calls onConfirm', () => {
    const onConfirm = vi.fn()
    renderModal({ onConfirm })
    fireEvent.click(screen.getByText('Eliminar 3 pedidos'))
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('clicking Cancelar button calls onClose', () => {
    const onClose = vi.fn()
    renderModal({ onClose })
    fireEvent.click(screen.getByText('Cancelar'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('Escape key calls onClose', () => {
    const onClose = vi.fn()
    renderModal({ onClose })
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('confirm button is disabled when isPending=true', () => {
    renderModal({ isPending: true })
    const confirmBtn = screen.getByText('Eliminar 3 pedidos')
    expect(confirmBtn).toBeDisabled()
  })

  it('shows default confirmLabel when not provided', () => {
    const defaults = {
      isOpen: true,
      onClose: vi.fn(),
      onConfirm: vi.fn(),
      title: 'Test',
      message: 'Test message',
    }
    render(<BulkConfirmModal {...defaults} />)
    expect(screen.getByText('Confirmar')).toBeInTheDocument()
  })
})
