/**
 * BulkConfirmModal — confirmation dialog before executing a bulk action.
 *
 * Shown before:
 *   - Bulk cancel: "¿Cancelar X pedidos?"
 *   - Any destructive bulk operation
 *
 * Props:
 *   isOpen: boolean
 *   onClose: () => void
 *   onConfirm: () => void | Promise<void>
 *   title: string
 *   message: string
 *   confirmLabel?: string (default "Confirmar")
 *   isPending?: boolean
 *
 * Accessibility: role="alertdialog", aria-modal, Escape key, focus management.
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { useEffect, useRef, useCallback } from 'react'
import { AlertTriangle } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/components/ui/Button'

export interface BulkConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void | Promise<void>
  title: string
  message: string
  confirmLabel?: string
  isPending?: boolean
}

export function BulkConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirmar',
  isPending = false,
}: BulkConfirmModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const cancelBtnRef = useRef<HTMLButtonElement>(null)
  const titleId = 'bulk-confirm-title'
  const descId = 'bulk-confirm-desc'

  // Focus cancel button on open (safer than confirm button for destructive actions)
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => cancelBtnRef.current?.focus(), 50)
    }
  }, [isOpen])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    },
    [isOpen, onClose],
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (!isOpen) return null

  return (
    /* Backdrop — NOT aria-hidden so screen readers can reach the dialog inside */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget && !isPending) onClose() }}
    >
      {/* Dialog */}
      <div
        ref={dialogRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        tabIndex={-1}
        className={cn(
          'relative w-full max-w-sm rounded-xl border border-border bg-card shadow-lg',
          'focus:outline-none mx-4',
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-5 py-6 flex flex-col items-center text-center gap-4">
          {/* Icon */}
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <AlertTriangle className="h-6 w-6 text-destructive" aria-hidden="true" />
          </div>

          {/* Title */}
          <h2 id={titleId} className="text-base font-semibold text-foreground">
            {title}
          </h2>

          {/* Message */}
          <p id={descId} className="text-sm text-muted-foreground">
            {message}
          </p>

          {/* Buttons */}
          <div className="flex gap-2 w-full justify-center mt-2">
            <button
              ref={cancelBtnRef}
              type="button"
              onClick={onClose}
              disabled={isPending}
              className={[
                'inline-flex items-center justify-center gap-2 font-medium',
                'transition-colors duration-150',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
                'disabled:pointer-events-none disabled:opacity-50',
                'bg-transparent text-foreground hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring',
                'h-8 px-3 text-sm rounded-md',
              ].join(' ')}
            >
              Cancelar
            </button>
            <Button
              variant="destructive"
              size="sm"
              onClick={onConfirm}
              disabled={isPending}
              loading={isPending}
            >
              {confirmLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
