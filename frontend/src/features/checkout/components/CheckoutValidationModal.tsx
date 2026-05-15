/**
 * CheckoutValidationModal — surfaces pre-checkout validation issues to the user.
 *
 * Behaviour (from spec checkout-validation-ui):
 *   - Hard block (carritoVacio || sinDireccion || productosInvalidos.length > 0):
 *       Shows only "Volver al carrito" — user CANNOT proceed.
 *   - Soft warning (stock_insuficiente || cambios_de_precio):
 *       Shows both "Volver al carrito" and "Continuar de todas formas".
 *       Clicking "Continuar" calls onConfirm and closes the modal.
 *
 * Accessibility (task 9.10):
 *   - Uses the existing shared <Modal> which provides role="dialog",
 *     aria-modal="true", aria-labelledby, and Escape-key close.
 *
 * Tailwind v4 tokens (task 9.9):
 *   - Uses semantic tokens: text-destructive, bg-destructive/10,
 *     text-yellow-600 (warning), bg-yellow-50 (warning bg).
 *   - No hardcoded color hex values.
 */

import { Modal } from '@/shared/components/ui/Modal'
import type { ValidarCarritoResponse } from '../types'

export interface CheckoutValidationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  validationResult: ValidarCarritoResponse | undefined
}

/**
 * CheckoutValidationModal
 *
 * Receives the raw ValidarCarritoResponse and determines severity internally.
 * Hard block = user MUST go back. Soft warning = user can proceed.
 */
export function CheckoutValidationModal({
  isOpen,
  onClose,
  onConfirm,
  validationResult,
}: CheckoutValidationModalProps) {
  if (!validationResult) return null

  // 9.3 — Determine block vs warning
  const hasInvalidProducts = validationResult.productos_invalidos.length > 0
  const isHardBlock =
    validationResult.carrito_vacio ||
    validationResult.sin_direccion ||
    hasInvalidProducts

  const hasStockIssues = validationResult.stock_insuficiente.length > 0
  const hasPriceChanges = validationResult.cambios_de_precio.length > 0

  const modalTitle = isHardBlock
    ? 'No es posible continuar con el pedido'
    : 'Hay cambios en tu carrito'

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={modalTitle}
    >
      <div className="flex flex-col gap-4">
        {/* ── Hard block: empty cart ─────────────────────────────── */}
        {validationResult.carrito_vacio && (
          <div
            role="alert"
            className="rounded-lg bg-destructive/10 border border-destructive/30 p-3 text-sm text-destructive"
          >
            <p className="font-semibold">Tu carrito está vacío</p>
            <p className="mt-1 text-destructive/80">
              Agregá al menos un producto antes de continuar.
            </p>
          </div>
        )}

        {/* ── Hard block: no delivery address ───────────────────── */}
        {validationResult.sin_direccion && (
          <div
            role="alert"
            className="rounded-lg bg-destructive/10 border border-destructive/30 p-3 text-sm text-destructive"
          >
            <p className="font-semibold">Sin dirección de entrega</p>
            <p className="mt-1 text-destructive/80">
              Necesitás agregar una dirección de entrega antes de hacer un pedido.
              Ir a &ldquo;Mis direcciones&rdquo; para configurarla.
            </p>
          </div>
        )}

        {/* ── Hard block: invalid products ─────────────────────── */}
        {/* 9.6 — Generic message for N unavailable products */}
        {hasInvalidProducts && (
          <div
            role="alert"
            className="rounded-lg bg-destructive/10 border border-destructive/30 p-3 text-sm text-destructive"
          >
            <p className="font-semibold">
              {validationResult.productos_invalidos.length === 1
                ? '1 producto ya no está disponible'
                : `${validationResult.productos_invalidos.length} productos ya no están disponibles`}
            </p>
            <p className="mt-1 text-destructive/80">
              Volvé al carrito y eliminá los productos no disponibles antes de continuar.
            </p>
          </div>
        )}

        {/* ── Soft warning: insufficient stock ──────────────────── */}
        {/* 9.4 — List each stock shortage with name, stock, qty */}
        {hasStockIssues && (
          <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-3 text-sm">
            <p className="font-semibold text-yellow-800">Stock insuficiente</p>
            <ul className="mt-2 space-y-1 text-yellow-700">
              {validationResult.stock_insuficiente.map((item) => (
                <li key={item.producto_id} className="flex justify-between gap-2">
                  <span className="font-medium">{item.nombre}</span>
                  <span className="text-yellow-600 whitespace-nowrap">
                    Pedido: {item.cantidad_solicitada} / Stock: {item.stock_actual}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ── Soft warning: price changes ────────────────────────── */}
        {/* 9.5 — List each price change with before/after values */}
        {hasPriceChanges && (
          <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-3 text-sm">
            <p className="font-semibold text-yellow-800">Cambios de precio</p>
            <p className="mt-1 text-yellow-700 text-xs">
              Los siguientes productos cambiaron de precio desde que los agregaste al carrito:
            </p>
            <ul className="mt-2 space-y-1 text-yellow-700">
              {validationResult.cambios_de_precio.map((item) => (
                <li key={item.producto_id} className="flex justify-between gap-2">
                  <span className="font-medium">Producto #{item.producto_id}</span>
                  <span className="text-yellow-600 whitespace-nowrap">
                    <span className="line-through mr-1">
                      ${Number(item.precio_carrito).toFixed(2)}
                    </span>
                    → ${Number(item.precio_actual).toFixed(2)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ── Action buttons ─────────────────────────────────────── */}
        <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 pt-2 border-t border-border">
          {/* "Volver al carrito" always present */}
          <button
            onClick={onClose}
            className="
              inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium
              border border-border bg-background text-foreground
              hover:bg-accent hover:text-accent-foreground
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
              transition-colors
            "
          >
            Volver al carrito
          </button>

          {/* 9.7 — Hard block: NO proceed button */}
          {/* 9.8 — Soft warning: show "Continuar de todas formas" */}
          {!isHardBlock && (
            <button
              onClick={() => {
                onConfirm()
                onClose()
              }}
              className="
                inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium
                bg-primary text-primary-foreground
                hover:bg-primary/90
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
                transition-colors
              "
            >
              Continuar de todas formas
            </button>
          )}
        </div>
      </div>
    </Modal>
  )
}
