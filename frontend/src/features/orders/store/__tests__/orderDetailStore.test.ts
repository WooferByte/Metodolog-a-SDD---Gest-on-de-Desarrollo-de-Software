/**
 * orderDetailStore tests.
 *
 * Verifies:
 *   - Initial state: isCancelModalOpen is false
 *   - openCancelModal sets isCancelModalOpen to true
 *   - closeCancelModal sets isCancelModalOpen to false
 *   - Store does NOT hold any order data (only UI state)
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useOrderDetailStore } from '../orderDetailStore'

describe('useOrderDetailStore', () => {
  beforeEach(() => {
    useOrderDetailStore.setState({ isCancelModalOpen: false })
  })

  it('has isCancelModalOpen = false as initial state', () => {
    expect(useOrderDetailStore.getState().isCancelModalOpen).toBe(false)
  })

  it('openCancelModal sets isCancelModalOpen to true', () => {
    useOrderDetailStore.getState().openCancelModal()
    expect(useOrderDetailStore.getState().isCancelModalOpen).toBe(true)
  })

  it('closeCancelModal sets isCancelModalOpen to false', () => {
    useOrderDetailStore.setState({ isCancelModalOpen: true })
    useOrderDetailStore.getState().closeCancelModal()
    expect(useOrderDetailStore.getState().isCancelModalOpen).toBe(false)
  })

  it('store state only contains UI fields (no order data)', () => {
    const state = useOrderDetailStore.getState()
    // Should only have UI-related keys + actions
    const stateKeys = Object.keys(state)
    expect(stateKeys).toContain('isCancelModalOpen')
    expect(stateKeys).toContain('openCancelModal')
    expect(stateKeys).toContain('closeCancelModal')
    // Must NOT store order data
    expect(stateKeys).not.toContain('order')
    expect(stateKeys).not.toContain('orderId')
    expect(stateKeys).not.toContain('detalles')
    expect(stateKeys).not.toContain('historial')
  })
})
