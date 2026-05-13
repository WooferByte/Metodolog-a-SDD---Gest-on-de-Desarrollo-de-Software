## Context

El layout actual tiene dos zonas de navegación activas simultáneamente:

| Componente | Qué muestra ahora | Qué debe mostrar |
|-----------|------------------|-----------------|
| `Navbar.tsx` | Hamburger + Brand + **navLinks** + user info + theme toggle | Hamburger + Brand + user info + theme toggle |
| `Sidebar.tsx` | navLinks con active state + backdrop mobile + persistent desktop | Sin cambios |

El Sidebar ya implementa el patrón correcto (mobile overlay / desktop persistente). El Navbar solo necesita dejar de duplicar los links.

## Cambio exacto en Navbar.tsx

**Eliminar**:
```tsx
import { useNavLinks } from '@/shared/hooks/useNavLinks'  // ← quitar
// ...
const navLinks = useNavLinks()                             // ← quitar
// ...
{navLinks.map((link) => (                                  // ← quitar bloque completo
  <Link key={link.to} to={link.to} ...>
    {link.label}
  </Link>
))}
```

**Actualizar JSDoc**: el comentario del componente describe links dinámicos por rol — reemplazar por la responsabilidad real post-fix.

**Resultado final del Navbar**:
```
[Hamburger] [Food Store]          [user@email] [Cerrar sesión] [🌙]
```

En mobile, el Sidebar arranca cerrado (overlay), el Hamburger lo abre. En desktop, el Sidebar arranca abierto (persistente), el Hamburger lo colapsa. El Navbar no cambia su apariencia por breakpoint — es siempre la misma barra fija arriba.

## No-changes

- `Sidebar.tsx` — sin tocar
- `useNavLinks.ts` — sin tocar (el hook sigue siendo usado por Sidebar)
- `Router.tsx` — sin tocar
- Stores — sin tocar
