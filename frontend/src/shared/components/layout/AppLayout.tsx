/**
 * AppLayout — main application shell.
 *
 * Renders:
 *   <Navbar>         top navigation bar (always visible)
 *   <Sidebar>        role-aware side navigation
 *   <main>           page content area (receives children)
 *   <Footer>         copyright footer
 *
 * Layout:
 *   - Column flex for full viewport height
 *   - When sidebar is open on lg+: flex-row for content + sidebar
 *   - main has id="main-content" for skip-nav accessibility
 *
 * Dark mode:
 *   - Does NOT manage dark mode class — that's handled in App.tsx
 *     to avoid double useEffect and keep this component pure layout.
 */

import type { ReactNode } from 'react'
import Navbar from '@/shared/components/Navbar'
import { Sidebar } from './Sidebar'
import { Footer } from './Footer'

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* Top navigation — spans full width */}
      <Navbar />

      {/* Content area: sidebar + main side by side on lg+ */}
      <div className="flex flex-1">
        <Sidebar />

        <main
          id="main-content"
          className="flex-1 overflow-auto"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>

      {/* Footer — spans full width */}
      <Footer />
    </div>
  )
}
