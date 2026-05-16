/**
 * useOrderDetailStore — Zustand v5 store for order detail page UI state.
 *
 * Design decision D3 (design.md): Modal open/close state lives in Zustand,
 * NOT in local useState, to allow it to be triggered from multiple components.
 *
 * CRITICAL: This store NEVER stores order data — only UI state.
 * All order data comes from TanStack Query via useOrderDetail.
 *
 * Zustand v5 syntax: create<T>()() with double parentheses.
 */

import { create } from 'zustand'

export interface OrderDetailState {
  isCancelModalOpen: boolean
  openCancelModal: () => void
  closeCancelModal: () => void
}

export const useOrderDetailStore = create<OrderDetailState>()((set) => ({
  isCancelModalOpen: false,
  openCancelModal: () => set({ isCancelModalOpen: true }),
  closeCancelModal: () => set({ isCancelModalOpen: false }),
}))
