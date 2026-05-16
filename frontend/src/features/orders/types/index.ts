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

/** Address snapshot embedded in each order — matches backend DireccionEntrega serialization */
export interface DireccionSnapshot {
  alias?: string | null
  linea1?: string | null
  ciudad?: string | null
  codigo_postal?: string | null
  piso?: string | null
  departamento?: string | null
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

// ---------------------------------------------------------------------------
// Detail types — extended for GET /api/v1/pedidos/{id}
// ---------------------------------------------------------------------------

/**
 * Detalle de línea del pedido — snapshot congelado al momento de compra.
 * NEVER use these to look up live product data — they are immutable snapshots.
 */
export interface OrderDetailItem {
  id: number
  producto_id: number
  /** Product name as it was at the time of purchase (snapshot) */
  nombre_snapshot: string
  cantidad: number
  /** Unit price as it was at the time of purchase (snapshot) */
  precio_snapshot: number
  /** INTEGER[] — IDs of excluded/modified ingredients (matches backend field name) */
  ingredientes_excluidos: number[] | null
}

/**
 * Entrada del historial de estados FSM del pedido.
 * Append-only — never updated or deleted.
 */
export interface OrderHistorialItem {
  id: number
  pedido_id: number
  estado_anterior_id: number | null
  estado_nuevo_id: number
  observacion: string | null
  /** ID of the user responsible for the transition */
  usuario_responsable_id: number | null
  /** Email included by the backend for display convenience; null if not available */
  usuario_email: string | null
  creado_en: string    // ISO 8601
}

/**
 * Detalle completo del pedido — response of GET /api/v1/pedidos/{id}.
 * Extends Order with line items and FSM history.
 */
export interface OrderDetail extends Order {
  detalles: OrderDetailItem[]
  historial: OrderHistorialItem[]
}
