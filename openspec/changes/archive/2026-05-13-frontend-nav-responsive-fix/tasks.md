## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — confirmar uso de tokens semánticos en los estilos que quedan en Navbar
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — confirmar que la estructura ARIA del Navbar sigue correcta sin los links
- [ ] 0.3 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — evaluar si los E2E tests de guards existentes se ven afectados

---

## 1. Leer estado actual de Navbar.tsx

- [ ] 1.1 Leer `frontend/src/shared/components/Navbar.tsx` completo — identificar exactamente las 3 líneas/bloques a eliminar: import `useNavLinks`, hook call `const navLinks = useNavLinks()`, y el bloque JSX `{navLinks.map(...)}`
- [ ] 1.2 Confirmar que no hay otros archivos que importen `useNavLinks` **desde** Navbar (el hook vive en `shared/hooks/` y sigue siendo usado por Sidebar — no se elimina)

---

## 2. Modificar Navbar.tsx

- [ ] 2.1 Eliminar la línea: `import { useNavLinks } from '@/shared/hooks/useNavLinks'`
- [ ] 2.2 Eliminar la línea: `const navLinks = useNavLinks()`
- [ ] 2.3 Eliminar el bloque JSX completo:
  ```tsx
  {navLinks.map((link) => (
    <Link
      key={link.to}
      to={link.to}
      className="text-gray-300 hover:text-white text-sm transition-colors"
    >
      {link.label}
    </Link>
  ))}
  ```
- [ ] 2.4 Actualizar el JSDoc del componente — reemplazar la descripción de "renders role-based nav links" por la responsabilidad real: el Navbar contiene hamburger, brand, user info y theme toggle; el Sidebar maneja toda la navegación
- [ ] 2.5 Verificar que los colores `bg-gray-900`, `text-gray-300`, `bg-red-600` del Navbar sean reemplazados por tokens semánticos del `@theme` si aplica (la skill tailwind-design-system lo exige). Nota: el Navbar usa `bg-gray-900` que es un color crudo — evaluar si corresponde usar un token semántico o si es intencional para la barra de nav (dark siempre).

---

## 3. Verificación

- [ ] 3.1 `cd frontend && npx tsc --noEmit` → 0 errores (el import eliminado no debe dejar referencias colgantes)
- [ ] 3.2 `cd frontend && npx vitest run` → 209/209 tests en verde (los tests de `useNavLinks` siguen pasando porque el hook no cambió)
- [ ] 3.3 Levantar `npm run dev` y verificar manualmente:
  - Navbar muestra: hamburger + "Food Store" + (si autenticado: email + "Cerrar sesión") + theme toggle
  - Navbar **NO** muestra links de navegación en ningún breakpoint
  - Sidebar sigue mostrando links correctos al abrirse
  - Hamburger del Navbar sigue abriendo/cerrando el Sidebar correctamente
- [ ] 3.4 Confirmar en mobile (< 1024px): Navbar sin links, hamburger abre Sidebar con todos los links
- [ ] 3.5 Confirmar en desktop (≥ 1024px): Sidebar persistente con links, Navbar limpio sin duplicación

---

## 4. Commit

- [ ] 4.1 `git add frontend/src/shared/components/Navbar.tsx`
- [ ] 4.2 `git commit -m "fix: remove nav links from Navbar — Sidebar handles all navigation"`
