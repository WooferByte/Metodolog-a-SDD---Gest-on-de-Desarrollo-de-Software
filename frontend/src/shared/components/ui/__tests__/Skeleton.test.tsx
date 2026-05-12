/**
 * Skeleton component tests.
 *
 * Tests:
 *   - Default (text) variant renders with animate-pulse
 *   - Circle variant has rounded-full class
 *   - Rect variant has rounded-lg class
 *   - className override
 *   - role="status" for screen readers
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Skeleton } from '../Skeleton'

describe('Skeleton', () => {
  it('renders with role="status"', () => {
    render(<Skeleton />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('default (text) variant has animate-pulse', () => {
    render(<Skeleton variant="text" />)
    const el = screen.getByRole('status')
    expect(el.className).toContain('animate-pulse')
  })

  it('circle variant has rounded-full', () => {
    render(<Skeleton variant="circle" />)
    const el = screen.getByRole('status')
    expect(el.className).toContain('rounded-full')
  })

  it('rect variant has rounded-lg', () => {
    render(<Skeleton variant="rect" />)
    const el = screen.getByRole('status')
    expect(el.className).toContain('rounded-lg')
  })

  it('text variant does not have rounded-full', () => {
    render(<Skeleton variant="text" />)
    const el = screen.getByRole('status')
    expect(el.className).not.toContain('rounded-full')
  })

  it('merges custom className', () => {
    render(<Skeleton className="h-32 w-full" />)
    const el = screen.getByRole('status')
    expect(el.className).toContain('h-32')
    expect(el.className).toContain('w-full')
  })
})
