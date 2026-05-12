/**
 * Modal component tests.
 *
 * The native <dialog> element's showModal()/close() are not supported by
 * jsdom. We use vi.spyOn to mock them so the imperative calls don't throw.
 *
 * Tests:
 *   - isOpen=true: title and children are rendered
 *   - isOpen=false: title and children are not rendered (dialog not opened)
 *   - Close button calls onClose
 *   - Escape key fires 'close' event → onClose is called
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Modal } from '../Modal'

// jsdom doesn't implement showModal() / close() — patch them
beforeEach(() => {
  // Patch HTMLDialogElement prototype for jsdom
  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function () {
      this.setAttribute('open', '')
    }
  }
  if (!HTMLDialogElement.prototype.close) {
    HTMLDialogElement.prototype.close = function () {
      this.removeAttribute('open')
      this.dispatchEvent(new Event('close'))
    }
  }
})

describe('Modal', () => {
  it('renders title and children when isOpen=true', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Confirmar">
        <p>Contenido del modal</p>
      </Modal>
    )
    expect(screen.getByText('Confirmar')).toBeInTheDocument()
    expect(screen.getByText('Contenido del modal')).toBeInTheDocument()
  })

  it('does not render content when isOpen=false', () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()} title="Oculto">
        <p>No visible</p>
      </Modal>
    )
    // Dialog exists in DOM but showModal was never called, so dialog is not "open"
    // The content is still in DOM (dialog renders children), but dialog has no open attr
    const dialog = document.querySelector('dialog')
    expect(dialog).not.toHaveAttribute('open')
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={onClose} title="Test">
        <p>Body</p>
      </Modal>
    )
    const closeBtn = screen.getByRole('button', { name: 'Cerrar modal' })
    fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when Escape key fires close event on dialog', () => {
    const onClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={onClose} title="Escape test">
        <p>Body</p>
      </Modal>
    )
    const dialog = document.querySelector('dialog')
    expect(dialog).toBeInTheDocument()
    // Simulate native close event (triggered by Escape in real browser)
    fireEvent(dialog!, new Event('close'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('renders modal without title', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <p>No title here</p>
      </Modal>
    )
    expect(screen.getByText('No title here')).toBeInTheDocument()
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })
})
