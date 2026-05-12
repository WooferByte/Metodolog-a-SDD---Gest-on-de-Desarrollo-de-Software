/**
 * useNavLinks — computes the visible navigation link list from current auth state + roles.
 *
 * Role priority (first match wins):
 *   ADMIN    → 6 links (full admin access)
 *   PEDIDOS  → 1 link  (order panel only)
 *   STOCK    → 3 links (inventory management)
 *   CLIENT   → 5 links (customer-facing)
 *   (none)   → 3 links (public, also shown while store hydrates)
 *
 * Usage:
 * ```tsx
 * const navLinks = useNavLinks()
 * navLinks.map(link => <Link to={link.to}>{link.label}</Link>)
 * ```
 */

import { useAuthStore } from '@/store/authStore'

export type NavLink = { label: string; to: string }

const PUBLIC_LINKS: NavLink[] = [
  { label: 'Catálogo', to: '/catalog' },
  { label: 'Iniciar sesión', to: '/login' },
  { label: 'Registrarse', to: '/register' },
]

const CLIENT_LINKS: NavLink[] = [
  { label: 'Catálogo', to: '/catalog' },
  { label: 'Carrito', to: '/cart' },
  { label: 'Mis Pedidos', to: '/orders' },
  { label: 'Mi Perfil', to: '/profile' },
  { label: 'Mis Direcciones', to: '/addresses' },
]

const STOCK_LINKS: NavLink[] = [
  { label: 'Productos', to: '/admin/productos' },
  { label: 'Categorías', to: '/admin/categorias' },
  { label: 'Ingredientes', to: '/admin/ingredientes' },
]

const PEDIDOS_LINKS: NavLink[] = [
  { label: 'Panel Pedidos', to: '/admin/pedidos' },
]

const ADMIN_LINKS: NavLink[] = [
  { label: 'Catálogo', to: '/catalog' },
  { label: 'Mis Pedidos', to: '/orders' },
  { label: 'Usuarios', to: '/admin/usuarios' },
  { label: 'Pedidos', to: '/admin/pedidos' },
  { label: 'Métricas', to: '/admin/metricas' },
  { label: 'Configuración', to: '/admin/configuracion' },
]

/**
 * Returns the nav link list appropriate for the current user's role.
 * While the store is still hydrating (_hasHydrated === false), falls back to public links
 * to avoid a flash of role-specific content before auth state is confirmed.
 */
export function useNavLinks(): NavLink[] {
  const _hasHydrated = useAuthStore((s) => s._hasHydrated)
  const roles = useAuthStore((s) => s.user?.roles ?? [])

  // Show public links until hydration completes
  if (!_hasHydrated) return PUBLIC_LINKS

  // Role priority: first match wins
  if (roles.includes('ADMIN')) return ADMIN_LINKS
  if (roles.includes('PEDIDOS')) return PEDIDOS_LINKS
  if (roles.includes('STOCK')) return STOCK_LINKS
  if (roles.includes('CLIENT')) return CLIENT_LINKS

  return PUBLIC_LINKS
}
