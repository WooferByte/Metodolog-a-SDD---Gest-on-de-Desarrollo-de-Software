/**
 * Orders feature — TypeScript type definitions.
 *
 * Aligned with backend schema (orders-api-endpoints):
 *   GET /api/v1/pedidos → { items: Order[], total, limit, offset }
 *
 * Note: estado_pedido_id arrives as a number from the backend JSON.
 * Do NOT use TypeScript enum for this field — see design.md D3.
 */

/** Single order from the backend API */
export interface Order {
  id: number
  usuario_id: number
  estado_pedido_id: number
  total: number
  creado_en: string           // ISO 8601 datetime string
  observacion: string | null
  /** Serialised address snapshot captured at order creation time */
  direccion_snapshot: DireccionSnapshot | null
  forma_pago_id: number
}

/** Address snapshot embedded in each order (captured at order-creation time) */
export interface DireccionSnapshot {
  calle: string
  numero: string
  ciudad: string
  provincia: string
  codigo_postal?: string
}

/**
 * Paginated orders response — matches backend PaginatedResponse schema:
 * { items, total, limit, offset }
 */
export interface OrdersPage {
  items: Order[]
  total: number
  limit: number
  offset: number
}

/** Parameters accepted by useOrders hook */
export interface UseOrdersParams {
  limit?: number
  offset?: number
  estadoId?: number | null
  /** Search by user email (admin only) */
  search?: string
  fechaDesde?: string
  fechaHasta?: string
}

/**
 * Metadata for a single order status ID.
 * colorClass uses Tailwind v4 semantic tokens — no hardcoded colors.
 */
export interface OrderStatusMeta {
  id: number
  label: string
  /** Tailwind classes using semantic @theme tokens for badge background + text */
  bgClass: string
  textClass: string
}
