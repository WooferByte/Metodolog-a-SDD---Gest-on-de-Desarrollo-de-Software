/**
 * Footer component tests.
 *
 * Tests:
 *   - Copyright text is present
 *   - Renders as <footer> element (role="contentinfo")
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Footer } from '../Footer'

describe('Footer', () => {
  it('renders copyright text', () => {
    render(<Footer />)
    expect(screen.getByText(/2026 Food Store/i)).toBeInTheDocument()
  })

  it('renders a <footer> element with contentinfo role', () => {
    render(<Footer />)
    const footer = screen.getByRole('contentinfo')
    expect(footer).toBeInTheDocument()
    expect(footer.tagName.toLowerCase()).toBe('footer')
  })

  it('displays "Todos los derechos reservados"', () => {
    render(<Footer />)
    expect(screen.getByText(/todos los derechos reservados/i)).toBeInTheDocument()
  })
})
