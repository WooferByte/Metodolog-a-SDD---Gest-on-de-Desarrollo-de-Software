/**
 * Card compound component tests.
 *
 * Tests:
 *   - Renders full compound (Card + CardHeader + CardContent + CardFooter)
 *   - CardTitle renders as h3
 *   - className override merges correctly on Card root
 *   - className override merges correctly on CardContent
 */

import '@testing-library/jest-dom'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../Card'

describe('Card compound component', () => {
  it('renders all sub-components', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Mi Tarjeta</CardTitle>
          <CardDescription>Descripción</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Contenido aquí</p>
        </CardContent>
        <CardFooter>
          <button>Guardar</button>
        </CardFooter>
      </Card>
    )

    expect(screen.getByText('Mi Tarjeta')).toBeInTheDocument()
    expect(screen.getByText('Descripción')).toBeInTheDocument()
    expect(screen.getByText('Contenido aquí')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar' })).toBeInTheDocument()
  })

  it('CardTitle renders as h3', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Título</CardTitle>
        </CardHeader>
      </Card>
    )
    const heading = screen.getByRole('heading', { level: 3 })
    expect(heading).toHaveTextContent('Título')
  })

  it('accepts and applies className override on Card', () => {
    const { container } = render(
      <Card className="custom-card-class">
        <CardContent>Body</CardContent>
      </Card>
    )
    // The first child of container is the Card root div
    const cardRoot = container.firstChild as HTMLElement
    expect(cardRoot.className).toContain('custom-card-class')
  })

  it('accepts className override on CardContent', () => {
    render(
      <Card>
        <CardContent className="extra-padding">Inner</CardContent>
      </Card>
    )
    // CardContent renders a div wrapping "Inner"
    // The text "Inner" is the direct child text node of CardContent's div
    const inner = screen.getByText('Inner')
    expect(inner.className).toContain('extra-padding')
  })
})
