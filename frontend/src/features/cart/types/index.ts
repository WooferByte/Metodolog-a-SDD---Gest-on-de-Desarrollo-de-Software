/**
 * Cart Feature Type Definitions
 *
 * CartUIItem extends CartItem with display helpers.
 * The base CartItem lives in @/store/types.ts — this layer adds
 * view-specific fields without polluting the store layer.
 */

import type { CartItem } from '@/store'

/**
 * CartUIItem — CartItem enriched with computed display helpers.
 * Used by components that need pre-formatted values (e.g. formattedPrice).
 */
export interface CartUIItem extends CartItem {
  /** Formatted price string — e.g. "$ 10,99" */
  formattedPrice: string
  /** Formatted subtotal (price × quantity) */
  formattedSubtotal: string
}

/**
 * Format a number as ARS currency string.
 * Uses Intl.NumberFormat for locale-aware formatting.
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount)
}

/**
 * Convert a CartItem to CartUIItem by adding display helpers.
 */
export function toCartUIItem(item: CartItem): CartUIItem {
  return {
    ...item,
    formattedPrice: formatCurrency(item.price),
    formattedSubtotal: formatCurrency(item.price * item.quantity),
  }
}
