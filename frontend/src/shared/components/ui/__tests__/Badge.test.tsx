/**
 * Badge component tests.
 *
 * Tests:
 *   - Default variant renders
 *   - Success variant applies success class
 *   - Error variant applies destructive class
 *   - Warning variant applies warning class
 *   - Info variant applies info class
 *   - className override
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from '../Badge'

describe('Badge', () => {
  it('renders badge text', () => {
    render(<Badge>Activo</Badge>)
    expect(screen.getByText('Activo')).toBeInTheDocument()
  })

  it('default variant has primary classes', () => {
    render(<Badge>Default</Badge>)
    const badge = screen.getByText('Default')
    expect(badge.className).toContain('bg-primary')
  })

  it('success variant applies success classes', () => {
    render(<Badge variant="success">Completado</Badge>)
    const badge = screen.getByText('Completado')
    expect(badge.className).toContain('bg-success')
  })

  it('error variant applies destructive classes', () => {
    render(<Badge variant="error">Error</Badge>)
    const badge = screen.getByText('Error')
    expect(badge.className).toContain('bg-destructive')
  })

  it('warning variant applies warning classes', () => {
    render(<Badge variant="warning">Alerta</Badge>)
    const badge = screen.getByText('Alerta')
    expect(badge.className).toContain('bg-warning')
  })

  it('info variant applies info classes', () => {
    render(<Badge variant="info">Info</Badge>)
    const badge = screen.getByText('Info')
    expect(badge.className).toContain('bg-info')
  })

  it('merges custom className', () => {
    render(<Badge className="ml-2">Tag</Badge>)
    expect(screen.getByText('Tag').className).toContain('ml-2')
  })
})
