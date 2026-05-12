/**
 * Modal — accessible modal dialog using native <dialog> element.
 *
 * Props:
 *   isOpen    — controls visibility; calls showModal()/close() on the <dialog>
 *   onClose   — called when user presses Escape or clicks the backdrop
 *   title     — modal heading (rendered as <h2>)
 *   children  — modal body content
 *
 * Accessibility:
 *   - Native <dialog> has built-in role="dialog" and focus management
 *   - aria-modal="true" for screen readers
 *   - Escape key closes (native <dialog> behavior)
 *   - Backdrop click closes via ::backdrop click detection
 *   - Focus returns to trigger when closed (browser-native)
 */

import { useEffect, useRef, type ReactNode } from 'react'
import { cn } from '@/shared/lib/utils'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  className?: string
}

export function Modal({ isOpen, onClose, title, children, className }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  // Open/close the native <dialog> element imperatively
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (isOpen) {
      if (!dialog.open) {
        dialog.showModal()
      }
    } else {
      if (dialog.open) {
        dialog.close()
      }
    }
  }, [isOpen])

  // Wire the native 'close' event (Escape key) to onClose callback
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    const handleClose = () => {
      onClose()
    }

    dialog.addEventListener('close', handleClose)
    return () => {
      dialog.removeEventListener('close', handleClose)
    }
  }, [onClose])

  // Backdrop click: detect click on the <dialog> element itself (outside content)
  const handleBackdropClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    const rect = dialogRef.current?.getBoundingClientRect()
    if (!rect) return
    const isInsideContent =
      e.clientX >= rect.left &&
      e.clientX <= rect.right &&
      e.clientY >= rect.top &&
      e.clientY <= rect.bottom
    if (!isInsideContent) {
      onClose()
    }
  }

  return (
    <dialog
      ref={dialogRef}
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
      onClick={handleBackdropClick}
      className={cn(
        // Reset default <dialog> styles
        'rounded-xl border border-border bg-card text-card-foreground',
        'shadow-lg p-0 max-w-lg w-full',
        // Backdrop
        'backdrop:bg-foreground/50',
        // Animation
        'open:animate-[fade-in_0.2s_ease-out]',
        className,
      )}
    >
      {/* Prevent backdrop click from propagating through content */}
      <div
        className="p-6 flex flex-col gap-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between">
            <h2
              id="modal-title"
              className="text-lg font-semibold text-foreground"
            >
              {title}
            </h2>
            <button
              onClick={onClose}
              aria-label="Cerrar modal"
              className={cn(
                'rounded-md p-1 text-muted-foreground',
                'hover:text-foreground hover:bg-accent transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              )}
            >
              {/* X icon */}
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Body */}
        <div>{children}</div>
      </div>
    </dialog>
  )
}
