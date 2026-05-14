/**
 * useCart — Aggregates the most common cart reads in one hook.
 *
 * Uses granular Zustand selectors — each selector subscribes to only
 * the specific value it needs, preventing unnecessary re-renders.
 *
 * IMPORTANT: Does NOT wrap actions. Components import actions directly
 * to avoid coupling the re-render cycle of reads with action updates.
 *
 * @example
 * const { items, totalItems, totalPrice, isEmpty } = useCart()
 */

import { useCartStore } from '@/store'

export function useCart() {
  // Granular selectors — each subscribes independently (rerender-derived-state)
  const items = useCartStore((s) => s.items)
  const totalItems = useCartStore((s) => s.totalItems())
  const totalPrice = useCartStore((s) => s.totalPrice())

  // Derived during render — no useEffect, no extra useState (rerender-derived-state-no-effect)
  const isEmpty = items.length === 0

  return { items, totalItems, totalPrice, isEmpty }
}
