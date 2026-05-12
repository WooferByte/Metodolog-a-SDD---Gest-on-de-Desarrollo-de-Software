/**
 * Sidebar component tests.
 *
 * Mocks:
 *   - useUIStore: controls sidebarOpen state
 *   - useNavLinks: returns fixed test links
 *   - useAuthStore: required by useNavLinks internals (mocked transitively)
 *
 * Tests:
 *   - Renders navigation links when sidebarOpen=true
 *   - Sidebar panel has -translate-x-full class when sidebarOpen=false
 *   - Active link has aria-current="page"
 */

import '@testing-library/jest-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// Mock stores and hooks BEFORE importing Sidebar
vi.mock('@/store/uiStore', () => ({
  useUIStore: vi.fn(),
}))

vi.mock('@/shared/hooks/useNavLinks', () => ({
  useNavLinks: vi.fn(),
}))

import { useUIStore } from '@/store/uiStore'
import { useNavLinks } from '@/shared/hooks/useNavLinks'
import { Sidebar } from '../Sidebar'

const mockUseUIStore = vi.mocked(useUIStore)
const mockUseNavLinks = vi.mocked(useNavLinks)

const testLinks = [
  { label: 'Catálogo', to: '/catalog' },
  { label: 'Iniciar sesión', to: '/login' },
]

function mockUIState(sidebarOpen: boolean) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  mockUseUIStore.mockImplementation((selector: (s: any) => any) => {
    const state = {
      sidebarOpen,
      toggleSidebar: vi.fn(),
    }
    return selector(state)
  })
  // Also mock setState for the auto-open useEffect
  ;(useUIStore as unknown as { setState: (s: unknown) => void }).setState = vi.fn()
}

beforeEach(() => {
  vi.clearAllMocks()
  mockUseNavLinks.mockReturnValue(testLinks)
  // Mock matchMedia to return false (mobile) by default
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
})

describe('Sidebar', () => {
  it('renders nav links when sidebarOpen=true', () => {
    mockUIState(true)
    render(
      <MemoryRouter initialEntries={['/catalog']}>
        <Sidebar />
      </MemoryRouter>
    )
    expect(screen.getByText('Catálogo')).toBeInTheDocument()
    expect(screen.getByText('Iniciar sesión')).toBeInTheDocument()
  })

  it('sidebar panel has -translate-x-full when sidebarOpen=false', () => {
    mockUIState(false)
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    const aside = screen.getByRole('complementary')
    expect(aside.className).toContain('-translate-x-full')
  })

  it('sidebar panel does NOT have -translate-x-full when sidebarOpen=true', () => {
    mockUIState(true)
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    const aside = screen.getByRole('complementary')
    expect(aside.className).not.toContain('-translate-x-full')
    expect(aside.className).toContain('translate-x-0')
  })

  it('active link has aria-current="page"', () => {
    mockUIState(true)
    render(
      <MemoryRouter initialEntries={['/catalog']}>
        <Sidebar />
      </MemoryRouter>
    )
    const activeLink = screen.getByRole('link', { name: 'Catálogo' })
    expect(activeLink).toHaveAttribute('aria-current', 'page')
  })

  it('inactive links do not have aria-current', () => {
    mockUIState(true)
    render(
      <MemoryRouter initialEntries={['/catalog']}>
        <Sidebar />
      </MemoryRouter>
    )
    const inactiveLink = screen.getByRole('link', { name: 'Iniciar sesión' })
    expect(inactiveLink).not.toHaveAttribute('aria-current')
  })
})
