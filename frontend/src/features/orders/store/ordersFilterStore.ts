/**
 * useOrdersFilterStore — Zustand v5 store for admin panel filter UI state.
 *
 * Design decision D4 (design.md): Filters are stored in Zustand (client state),
 * NOT in URL search params and NOT duplicated from server data.
 *
 * Rules:
 * - This store ONLY holds UI filter state — never server/API data.
 * - The store has NO persist middleware: filters reset on tab reload,
 *   which is acceptable for an internal admin panel.
 * - Zustand v5 syntax: create<T>()() with double parentheses.
 *
 * Extended (frontend-orders-management-admin):
 * - usuarioEmail: advanced filter for user email lookup
 * - totalMin / totalMax: price range filters
 */

import { create } from 'zustand'

export interface OrdersFilterState {
  estadoId: number | null
  search: string
  fechaDesde: string
  fechaHasta: string
  // Extended filters for management panel
  usuarioEmail: string
  totalMin: number | null
  totalMax: number | null
  // Actions
  setEstadoId: (id: number | null) => void
  setSearch: (search: string) => void
  setFechaDesde: (fecha: string) => void
  setFechaHasta: (fecha: string) => void
  setUsuarioEmail: (email: string) => void
  setTotalMin: (v: number | null) => void
  setTotalMax: (v: number | null) => void
  resetFilters: () => void
}

const initialState = {
  estadoId: null,
  search: '',
  fechaDesde: '',
  fechaHasta: '',
  usuarioEmail: '',
  totalMin: null,
  totalMax: null,
}

export const useOrdersFilterStore = create<OrdersFilterState>()((set) => ({
  ...initialState,

  setEstadoId: (id) => set({ estadoId: id }),
  setSearch: (search) => set({ search }),
  setFechaDesde: (fecha) => set({ fechaDesde: fecha }),
  setFechaHasta: (fecha) => set({ fechaHasta: fecha }),
  setUsuarioEmail: (email) => set({ usuarioEmail: email }),
  setTotalMin: (v) => set({ totalMin: v }),
  setTotalMax: (v) => set({ totalMax: v }),

  resetFilters: () => set(initialState),
}))
