/**
 * Footer — application footer with copyright notice.
 *
 * Uses semantic HTML <footer> element with proper ARIA landmark.
 * All colors use semantic design tokens from @theme.
 */

export function Footer() {
  return (
    <footer
      className="border-t border-border bg-card text-muted-foreground"
      role="contentinfo"
    >
      <div className="mx-auto max-w-screen-xl px-4 py-4 text-center text-sm">
        &copy; 2026 Food Store. Todos los derechos reservados.
      </div>
    </footer>
  )
}
