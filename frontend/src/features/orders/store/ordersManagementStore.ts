/**
 * ordersManagementStore — Zustand v5 store for bulk selection UI state.
 *
 * Responsibilities (UI state only — never server data):
 *   - selectedIds: Set<number> — which order IDs are checked
 *   - isBulkPending: boolean   — optimistic pending flag while bulk op runs
 *
 * Derived selectors (computed at call site):
 *   - isAllSelected(ids): all given IDs are in selectedIds
 *   - isIndeterminate(ids): some but not all IDs selected
 *
 * Rules:
 *   - Zustand v5: create<T>()() double parentheses
 *   - Set is serialised correctly for equality checks
 *   - No server data ever stored here
 */

import { create } from 'zustand'

export interface OrdersManagementState {
  selectedIds: Set<number>
  isBulkPending: boolean

  // Actions
  toggleId: (id: number) => void
  setAllIds: (ids: number[]) => void
  clearAll: () => void
  setIsBulkPending: (v: boolean) => void

  // Derived helpers (stateless — depend on snapshot param)
  isAllSelected: (ids: number[]) => boolean
  isIndeterminate: (ids: number[]) => boolean
}

export const useOrdersManagementStore = create<OrdersManagementState>()((set, get) => ({
  selectedIds: new Set<number>(),
  isBulkPending: false,

  toggleId: (id) =>
    set((state) => {
      const next = new Set(state.selectedIds)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return { selectedIds: next }
    }),

  setAllIds: (ids) => set({ selectedIds: new Set(ids) }),

  clearAll: () => set({ selectedIds: new Set<number>() }),

  setIsBulkPending: (v) => set({ isBulkPending: v }),

  // Returns true only if ids is non-empty and ALL are selected
  isAllSelected: (ids) => {
    if (ids.length === 0) return false
    const { selectedIds } = get()
    return ids.every((id) => selectedIds.has(id))
  },

  // Returns true if SOME (but not all) ids are selected
  isIndeterminate: (ids) => {
    if (ids.length === 0) return false
    const { selectedIds } = get()
    const someSelected = ids.some((id) => selectedIds.has(id))
    const allSelected  = ids.every((id) => selectedIds.has(id))
    return someSelected && !allSelected
  },
}))
