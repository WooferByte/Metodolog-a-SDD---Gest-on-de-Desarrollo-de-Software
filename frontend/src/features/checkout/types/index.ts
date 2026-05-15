/**
 * Type definitions for the checkout pre-validation feature.
 *
 * These types mirror the backend Pydantic schemas from pedidos/schemas.py.
 * Backend uses snake_case; we keep snake_case here to stay 1:1 with the API
 * response without any mapping layer.
 */

// ---------------------------------------------------------------------------
// Request types (sent to POST /api/v1/pedidos/validar)
// ---------------------------------------------------------------------------

/**
 * A single cart item sent for pre-checkout validation.
 * Maps to backend ValidarItemRequest.
 */
export interface ValidarItemRequest {
  /** Product primary key. */
  producto_id: number
  /** Quantity requested by the user. */
  cantidad: number
  /** Price stored in the Zustand cart at the time of addItem(). */
  precio_carrito: number
}

/**
 * Request body for the validation endpoint.
 * Maps to backend ValidarCarritoRequest.
 */
export interface ValidarCarritoRequest {
  /** Non-empty list of cart items. */
  items: ValidarItemRequest[]
  /** ID of the selected delivery address. */
  direccion_id: number
}

// ---------------------------------------------------------------------------
// Response types (received from POST /api/v1/pedidos/validar)
// ---------------------------------------------------------------------------

/**
 * Describes a single stock-shortage issue.
 * Maps to backend StockInsuficienteItem.
 */
export interface StockInsuficienteItem {
  producto_id: number
  nombre: string
  stock_actual: number
  cantidad_solicitada: number
}

/**
 * Describes a single price-drift issue.
 * Maps to backend CambioPrecioItem.
 */
export interface CambioPrecioItem {
  producto_id: number
  /** Price stored in the cart when the product was added. */
  precio_carrito: number
  /** Current price from the database. */
  precio_actual: number
}

/**
 * Structured validation report returned by the validation endpoint.
 * Maps to backend ValidarCarritoResponse.
 *
 * HTTP 200: soft warnings only (stock/price issues or clean result).
 * HTTP 422: hard blocks (empty cart / no address) — these never reach this type;
 *           they are thrown as errors in the mutation's onError handler.
 */
export interface ValidarCarritoResponse {
  /** Products where requested quantity exceeds available stock. */
  stock_insuficiente: StockInsuficienteItem[]
  /** Product IDs that are unavailable (soft-deleted, disponible=false, or not found). */
  productos_invalidos: number[]
  /** Products where the cart price drifted from the current DB price by > 0.01. */
  cambios_de_precio: CambioPrecioItem[]
  /** True if the submitted items list was empty (hard block flag). */
  carrito_vacio: boolean
  /** True if the user has no active delivery addresses (hard block flag). */
  sin_direccion: boolean
}
