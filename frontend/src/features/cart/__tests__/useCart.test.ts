/**
 * useCart hook tests
 *
 * Verifies:
 * - isEmpty is true when cart is empty, false when has items
 * - totalPrice sums correctly
 * - totalItems sums quantities
 */

import '@testing-library/jest-dom'
import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useCart } from '@/features/cart/hooks/useCart'
import { useCartStore } from '@/store'

describe('useCart', () => {
  beforeEach(() => {
    localStorage.clear()
    useCartStore.setState({ items: [] })
  })

  it('isEmpty is true when cart has no items', () => {
    const { result } = renderHook(() => useCart())
    expect(result.current.isEmpty).toBe(true)
    expect(result.current.items).toHaveLength(0)
    expect(result.current.totalItems).toBe(0)
    expect(result.current.totalPrice).toBe(0)
  })

  it('isEmpty is false when cart has items', () => {
    useCartStore.setState({
      items: [
        { productId: 'p1', name: 'Pizza', price: 10.99, quantity: 2 },
      ],
    })
    const { result } = renderHook(() => useCart())
    expect(result.current.isEmpty).toBe(false)
    expect(result.current.items).toHaveLength(1)
  })

  it('totalPrice sums price × quantity across all items', () => {
    useCartStore.setState({
      items: [
        { productId: 'p1', name: 'Pizza', price: 10.00, quantity: 2 },
        { productId: 'p2', name: 'Calzone', price: 15.00, quantity: 1 },
      ],
    })
    const { result } = renderHook(() => useCart())
    expect(result.current.totalPrice).toBe(35.00) // (10*2) + (15*1)
  })

  it('totalItems sums quantities of all items', () => {
    useCartStore.setState({
      items: [
        { productId: 'p1', name: 'Pizza', price: 10.99, quantity: 3 },
        { productId: 'p2', name: 'Calzone', price: 12.99, quantity: 2 },
      ],
    })
    const { result } = renderHook(() => useCart())
    expect(result.current.totalItems).toBe(5) // 3 + 2
  })

  it('reflects store updates reactively', () => {
    const { result, rerender } = renderHook(() => useCart())
    expect(result.current.isEmpty).toBe(true)

    useCartStore.getState().addItem({ productId: 'p1', name: 'Pizza', price: 9.99, quantity: 1 })
    rerender()

    expect(result.current.isEmpty).toBe(false)
    expect(result.current.totalItems).toBe(1)
  })
})
