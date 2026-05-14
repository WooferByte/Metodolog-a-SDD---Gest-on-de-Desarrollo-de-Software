/**
 * ToastContainer — Global toast notification renderer
 *
 * Consumes the `toasts` slice from `useUIStore` and renders each toast
 * with auto-dismiss and manual close.
 *
 * Auto-dismiss durations (can be overridden per-toast via `toast.duration`):
 *   - success / info  → 4000ms
 *   - warning         → 5000ms
 *   - error           → 6000ms
 *
 * Max simultaneous toasts: 5 (oldest removed automatically)
 * Position: fixed bottom-4 right-4 (does not block page content)
 */

import { useEffect } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { useUIStore } from '@/store/uiStore'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  message: string
  type: ToastType
  duration?: number
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_TOASTS = 5

const DEFAULT_DURATION: Record<ToastType, number> = {
  success: 4000,
  info: 4000,
  warning: 5000,
  error: 6000,
}

// ---------------------------------------------------------------------------
// Styling maps (Tailwind v4 — semantic classes)
// ---------------------------------------------------------------------------

const TOAST_STYLES: Record<ToastType, string> = {
  success:
    'border-border bg-card text-foreground',
  error:
    'border-destructive/30 bg-destructive/10 text-foreground',
  warning:
    'border-border bg-muted text-foreground',
  info:
    'border-border bg-card text-foreground',
}

const ICON_STYLES: Record<ToastType, string> = {
  success: 'text-foreground',
  error: 'text-destructive',
  warning: 'text-muted-foreground',
  info: 'text-muted-foreground',
}

const CLOSE_STYLES: Record<ToastType, string> = {
  success: 'text-muted-foreground hover:text-foreground',
  error: 'text-destructive/70 hover:text-destructive',
  warning: 'text-muted-foreground hover:text-foreground',
  info: 'text-muted-foreground hover:text-foreground',
}

// ---------------------------------------------------------------------------
// Icon component
// ---------------------------------------------------------------------------

function ToastIcon({ type }: { type: ToastType }) {
  const cls = `shrink-0 ${ICON_STYLES[type]}`
  const size = 20

  switch (type) {
    case 'success':
      return <CheckCircle2 size={size} className={cls} aria-hidden="true" />
    case 'error':
      return <XCircle size={size} className={cls} aria-hidden="true" />
    case 'warning':
      return <AlertTriangle size={size} className={cls} aria-hidden="true" />
    case 'info':
      return <Info size={size} className={cls} aria-hidden="true" />
  }
}

// ---------------------------------------------------------------------------
// Single Toast item
// ---------------------------------------------------------------------------

interface ToastItemProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const duration = toast.duration ?? DEFAULT_DURATION[toast.type]

  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id)
    }, duration)

    return () => clearTimeout(timer)
  }, [toast.id, duration, onRemove])

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className={`flex items-start gap-3 rounded-lg border p-4 shadow-sm ${TOAST_STYLES[toast.type]}`}
    >
      <ToastIcon type={toast.type} />

      <p className="flex-1 text-sm font-medium leading-snug">
        {String(toast.message)}
      </p>

      <button
        onClick={() => onRemove(toast.id)}
        aria-label="Cerrar notificación"
        className={`shrink-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current focus-visible:ring-offset-1 ${CLOSE_STYLES[toast.type]}`}
      >
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// ToastContainer
// ---------------------------------------------------------------------------

export function ToastContainer() {
  const toasts = useUIStore((s) => s.toasts) as Toast[]
  const removeToast = useUIStore((s) => s.removeToast)

  // Enforce max limit — keep only the newest MAX_TOASTS
  const visible = toasts.length > MAX_TOASTS
    ? toasts.slice(toasts.length - MAX_TOASTS)
    : toasts

  if (visible.length === 0) return null

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2"
      aria-label="Notificaciones"
    >
      {visible.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onRemove={removeToast}
        />
      ))}
    </div>
  )
}
