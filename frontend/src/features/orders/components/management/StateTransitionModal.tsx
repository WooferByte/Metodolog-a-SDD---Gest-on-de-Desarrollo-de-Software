/**
 * StateTransitionModal — modal for changing an order's FSM state.
 *
 * Single order mode:
 *   - Shows radio inputs for each valid transition from FSM_TRANSITIONS
 *   - Submits via useAdvanceOrderState mutation
 *   - Inline error on failure; success toast + onSuccess() callback
 *
 * Bulk mode (isBulkMode=true):
 *   - Shows same radio inputs, applies to all bulkOrderIds
 *   - Calls bulkAdvanceState from useBulkOrderActions
 *
 * Terminal state: shows a message instead of radio inputs.
 *
 * Accessibility: role="dialog", aria-modal, aria-labelledby, Escape key.
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/components/ui/Button'
import { useAdvanceOrderState } from '@/features/orders/hooks/useAdvanceOrderState'
import { useBulkOrderActions } from '@/features/orders/hooks/useBulkOrderActions'
import {
  getValidTransitions,
  isTerminalState,
  ORDER_STATUS_LABELS,
} from '@/features/orders/constants/orderTransitions'

export interface StateTransitionModalProps {
  orderId: number
  currentStatusId: number
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
  /** Bulk mode: apply state change to multiple orders */
  isBulkMode?: boolean
  bulkOrderIds?: number[]
}

export function StateTransitionModal({
  orderId,
  currentStatusId,
  isOpen,
  onClose,
  onSuccess,
  isBulkMode = false,
  bulkOrderIds = [],
}: StateTransitionModalProps) {
  const [selectedStateId, setSelectedStateId] = useState<number | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const firstRadioRef = useRef<HTMLInputElement>(null)

  const advanceMutation = useAdvanceOrderState()
  const { bulkAdvanceState } = useBulkOrderActions()

  const validTransitions = getValidTransitions(currentStatusId)
  const terminal = isTerminalState(currentStatusId)

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedStateId(null)
      setErrorMessage(null)
      // Focus first radio on open (or dialog if no radios)
      setTimeout(() => {
        firstRadioRef.current?.focus() ?? dialogRef.current?.focus()
      }, 50)
    }
  }, [isOpen])

  // Escape key handler
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

  const handleSubmit = async () => {
    if (selectedStateId == null) return
    setErrorMessage(null)

    if (isBulkMode) {
      const ids = bulkOrderIds.length > 0 ? bulkOrderIds : [orderId]
      await bulkAdvanceState(ids, selectedStateId)
      onSuccess?.()
      onClose()
    } else {
      try {
        await advanceMutation.mutateAsync({ orderId, nuevoEstadoId: selectedStateId })
        onSuccess?.()
        onClose()
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Error al cambiar el estado'
        setErrorMessage(msg)
      }
    }
  }

  if (!isOpen) return null

  const titleId = 'state-transition-modal-title'
  const isPending = advanceMutation.isPending

  const targetCount = isBulkMode && bulkOrderIds.length > 1
    ? `${bulkOrderIds.length} pedidos`
    : `pedido #${orderId}`

  return (
    /* Backdrop — NOT aria-hidden so screen readers can reach the dialog inside */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={cn(
          'relative w-full max-w-md rounded-xl border border-border bg-card shadow-lg',
          'focus:outline-none',
          'mx-4',
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <header className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 id={titleId} className="text-base font-semibold text-foreground">
            Cambiar estado — {targetCount}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar modal"
            className={cn(
              'h-8 w-8 rounded-md inline-flex items-center justify-center',
              'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            )}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </header>

        {/* Body */}
        <div className="px-5 py-4 space-y-4">
          {/* Current state info */}
          <p className="text-sm text-muted-foreground">
            Estado actual:{' '}
            <span className="font-medium text-foreground">
              {ORDER_STATUS_LABELS[currentStatusId] ?? 'Desconocido'}
            </span>
          </p>

          {terminal ? (
            <p className="text-sm text-muted-foreground bg-muted rounded-lg px-4 py-3">
              Este pedido está en un estado terminal y no admite más transiciones.
            </p>
          ) : validTransitions.length === 0 ? (
            <p className="text-sm text-muted-foreground bg-muted rounded-lg px-4 py-3">
              No hay transiciones disponibles para este estado.
            </p>
          ) : (
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium text-foreground mb-2">
                Nuevo estado
              </legend>
              {validTransitions.map((stateId, idx) => (
                <label
                  key={stateId}
                  className={cn(
                    'flex items-center gap-3 rounded-lg border px-4 py-3 cursor-pointer',
                    'transition-colors duration-100',
                    selectedStateId === stateId
                      ? 'border-primary bg-primary/5 text-foreground'
                      : 'border-border bg-background text-foreground hover:bg-accent/50',
                  )}
                >
                  <input
                    ref={idx === 0 ? firstRadioRef : undefined}
                    type="radio"
                    name="nuevo-estado"
                    value={stateId}
                    checked={selectedStateId === stateId}
                    onChange={() => setSelectedStateId(stateId)}
                    className="h-4 w-4 accent-primary"
                    aria-label={`Cambiar a ${ORDER_STATUS_LABELS[stateId] ?? stateId}`}
                  />
                  <span className="text-sm font-medium">
                    {ORDER_STATUS_LABELS[stateId] ?? `Estado ${stateId}`}
                  </span>
                </label>
              ))}
            </fieldset>
          )}

          {/* Inline API error */}
          {errorMessage && (
            <p role="alert" className="text-sm text-destructive bg-destructive/10 rounded-lg px-4 py-2">
              {errorMessage}
            </p>
          )}
        </div>

        {/* Footer */}
        {!terminal && validTransitions.length > 0 && (
          <footer className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
            <Button variant="ghost" size="sm" onClick={onClose} disabled={isPending}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSubmit}
              disabled={selectedStateId == null || isPending}
              loading={isPending}
            >
              Confirmar cambio
            </Button>
          </footer>
        )}
      </div>
    </div>
  )
}
