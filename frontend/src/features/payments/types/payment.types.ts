/**
 * Payment feature — TypeScript type definitions.
 *
 * Includes:
 *   - PaymentMethod union type
 *   - PaymentStatus union type
 *   - PaymentState interface (Zustand store shape)
 *   - PaymentMethodOption (for the selector component)
 *   - Global window.MercadoPago declaration (CDN-loaded SDK)
 */

// ---------------------------------------------------------------------------
// Union types
// ---------------------------------------------------------------------------

/** Supported payment method identifiers */
export type PaymentMethod = 'mercadopago' | 'cash' | null

/**
 * Payment flow status transitions:
 *   idle → creating_order → creating_preference → waiting_payment → success | error | pending
 */
export type PaymentStatus =
  | 'idle'
  | 'creating_order'
  | 'creating_preference'
  | 'waiting_payment'
  | 'success'
  | 'error'
  | 'pending'

// ---------------------------------------------------------------------------
// Store shape
// ---------------------------------------------------------------------------

/** Full state + actions for the Zustand payment store */
export interface PaymentState {
  // State fields
  method: PaymentMethod
  pedidoId: number | null
  preferenceId: string | null
  pagoId: number | null
  initPoint: string | null
  status: PaymentStatus
  error: string | null

  // Actions
  setMethod: (method: PaymentMethod) => void
  setPedidoId: (id: number) => void
  setPreference: (preferenceId: string, pagoId: number, initPoint: string) => void
  setStatus: (status: PaymentStatus) => void
  setError: (error: string | null) => void
  reset: () => void
}

// ---------------------------------------------------------------------------
// Payment method option (for PaymentMethodSelector)
// ---------------------------------------------------------------------------

/** Single option rendered by PaymentMethodSelector */
export interface PaymentMethodOption {
  id: 'mercadopago' | 'cash' | 'card'
  label: string
  description: string
  icon: string
  enabled: boolean
}

// ---------------------------------------------------------------------------
// API response types (matching backend schemas)
// ---------------------------------------------------------------------------

/** Response from POST /api/v1/pedidos — partial, we only need id */
export interface CreateOrderResponse {
  id: number
  [key: string]: unknown
}

/** Response from POST /api/v1/pagos/crear-preferencia */
export interface CreatePreferenceResponse {
  init_point: string
  preference_id: string
  pago_id: number
}

/** Request body for POST /api/v1/pagos/crear-preferencia */
export interface CreatePreferenceRequest {
  pedido_id: number
}

/** Response from GET /api/v1/pagos/{pedido_id}/status */
export interface PaymentStatusResponse {
  pago_id: number
  pedido_id: number
  mercadopago_id: string | null
  preference_id: string | null
  estado: string
  monto: number
  creado_en: string
  actualizado_en: string
}

// ---------------------------------------------------------------------------
// Global window.MercadoPago declaration (CDN script — not npm package)
// ---------------------------------------------------------------------------

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    MercadoPago: any
  }
}
