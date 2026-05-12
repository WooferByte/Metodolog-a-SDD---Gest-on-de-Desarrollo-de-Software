/**
 * Button component tests.
 *
 * Tests:
 *   - Default render (primary variant)
 *   - Destructive variant applies correct class
 *   - Loading state: spinner shown + button disabled
 *   - Disabled prop disables button
 *   - className override is applied
 *   - Click handler is called when not disabled
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../Button'

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })

  it('applies destructive variant classes', () => {
    render(<Button variant="destructive">Delete</Button>)
    const btn = screen.getByRole('button', { name: 'Delete' })
    expect(btn.className).toMatch(/destructive/)
  })

  it('shows loading spinner and disables button when loading=true', () => {
    render(<Button loading>Saving</Button>)
    const btn = screen.getByRole('button', { name: 'Saving' })
    expect(btn).toBeDisabled()
    expect(btn).toHaveAttribute('aria-busy', 'true')
    // SVG spinner should be in the DOM
    expect(btn.querySelector('svg')).toBeInTheDocument()
  })

  it('disables button when disabled=true', () => {
    render(<Button disabled>Submit</Button>)
    expect(screen.getByRole('button', { name: 'Submit' })).toBeDisabled()
  })

  it('merges custom className', () => {
    render(<Button className="my-custom">Test</Button>)
    const btn = screen.getByRole('button', { name: 'Test' })
    expect(btn.className).toContain('my-custom')
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button', { name: 'Click' }))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not call onClick when disabled', () => {
    const handleClick = vi.fn()
    render(<Button disabled onClick={handleClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button', { name: 'Click' }))
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('applies secondary variant', () => {
    render(<Button variant="secondary">Secondary</Button>)
    const btn = screen.getByRole('button', { name: 'Secondary' })
    expect(btn.className).toMatch(/secondary/)
  })
})
