/**
 * FSM transition matrices for order states.
 *
 * Two matrices are maintained:
 *
 *   FSM_TRANSITIONS — full matrix per the task spec (including cancel option for ADMIN):
 *     1=PENDIENTE    → [6]           (solo cancelar vía endpoint DELETE)
 *     2=CONFIRMADO   → [3, 6]        (preparar o cancelar)
 *     3=EN_PREPARACIÓN → [4]         (en camino)
 *     4=EN_CAMINO    → [5]           (entregado)
 *     5=ENTREGADO    → []            (terminal)
 *     6=CANCELADO    → []            (terminal)
 *
 *   VALID_TRANSITIONS — admin-advance matrix (excludes cancel; cancel uses DELETE endpoint):
 *     1=PENDIENTE      → [] (system/webhook only)
 *     2=CONFIRMADO     → [3]
 *     3=EN_PREPARACIÓN → [4]
 *     4=EN_CAMINO      → [5]
 *     5=ENTREGADO      → []
 *     6=CANCELADO      → []
 *
 * StateTransitionModal uses FSM_TRANSITIONS (shows cancel option too).
 * Legacy components can continue using VALID_TRANSITIONS.
 */

/** Full FSM matrix — includes CANCELADO (6) as valid target where applicable */
export const FSM_TRANSITIONS: Record<number, number[]> = {
  1: [6],       // PENDIENTE — can only be cancelled
  2: [3, 6],    // CONFIRMADO → EN_PREPARACIÓN or CANCELADO
  3: [4],       // EN_PREPARACIÓN → EN_CAMINO
  4: [5],       // EN_CAMINO → ENTREGADO
  5: [],        // ENTREGADO (terminal)
  6: [],        // CANCELADO (terminal)
}

/**
 * VALID_TRANSITIONS — FSM transition matrix for order states.
 *
 * Maps each estado_pedido_id to the list of valid next states that ADMIN/PEDIDOS
 * can advance to manually. CLIENT-only transitions (e.g. PENDIENTE → CANCELADO)
 * are handled separately via the cancel endpoint.
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
 * Returns the valid transition targets for the given estado_pedido_id
 * using the full FSM matrix (including cancel option).
 */
export function getValidTransitions(currentStatusId: number): number[] {
  return FSM_TRANSITIONS[currentStatusId] ?? []
}

/**
 * Returns true if the given estado_pedido_id is a terminal state
 * (ENTREGADO or CANCELADO) with no valid transitions.
 */
export function isTerminalState(estadoId: number): boolean {
  return TERMINAL_STATES.has(estadoId)
}

/** Human-readable labels for each estado_pedido_id */
export const ORDER_STATUS_LABELS: Record<number, string> = {
  1: 'Pendiente',
  2: 'Confirmado',
  3: 'En preparación',
  4: 'En camino',
  5: 'Entregado',
  6: 'Cancelado',
}
