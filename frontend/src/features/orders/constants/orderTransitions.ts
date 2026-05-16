/**
 * VALID_TRANSITIONS — FSM transition matrix for order states.
 *
 * Maps each estado_pedido_id to the list of valid next states that ADMIN/PEDIDOS
 * can advance to manually. CLIENT-only transitions (e.g. PENDIENTE → CANCELADO)
 * are handled separately via the cancel endpoint.
 *
 * Based on the FSM spec in docs/Integrador.txt and design.md:
 *
 *   1 = PENDIENTE      → confirmed by system/webhook only (not manual)
 *   2 = CONFIRMADO     → [3] EN_PREPARACIÓN (ADMIN/PEDIDOS)
 *   3 = EN_PREPARACIÓN → [4] EN_CAMINO      (ADMIN/PEDIDOS)
 *   4 = EN_CAMINO      → [5] ENTREGADO      (ADMIN/PEDIDOS)
 *   5 = ENTREGADO      → [] (terminal)
 *   6 = CANCELADO      → [] (terminal)
 *
 * Note: State 1 (PENDIENTE) → 2 (CONFIRMADO) is triggered by the MercadoPago webhook,
 * not by manual admin action. So PENDIENTE shows no manual advance option.
 *
 * ADMIN can cancel CONFIRMADO (2 → 6) via the cancel endpoint, not this matrix.
 */
export const VALID_TRANSITIONS: Record<number, number[]> = {
  1: [],    // PENDIENTE — no manual advance (system/webhook only)
  2: [3],   // CONFIRMADO → EN_PREPARACIÓN
  3: [4],   // EN_PREPARACIÓN → EN_CAMINO
  4: [5],   // EN_CAMINO → ENTREGADO
  5: [],    // ENTREGADO (terminal)
  6: [],    // CANCELADO (terminal)
}

/** IDs of terminal states — no further transitions possible */
export const TERMINAL_STATES: ReadonlySet<number> = new Set([5, 6])

/**
 * Returns true if the given estado_pedido_id is a terminal state
 * (ENTREGADO or CANCELADO) with no valid transitions.
 */
export function isTerminalState(estadoId: number): boolean {
  return TERMINAL_STATES.has(estadoId)
}
