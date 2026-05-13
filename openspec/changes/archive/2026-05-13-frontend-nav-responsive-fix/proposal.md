## Why

El Navbar actual duplica todos los links de navegación que el Sidebar ya muestra, en todos los breakpoints simultáneamente. El profesor señaló que es mala práctica tener dos navs con el mismo contenido. La causa raíz es que `frontend-navigation-by-role` y `frontend-layout-components-shared` se implementaron sin coordinación: ambos consumen `useNavLinks()` y ambos renderizan los links sin delimitar responsabilidades por breakpoint. El fix correcto es eliminar los links del Navbar completamente — el Sidebar (con su hamburguesa ya integrada en el Navbar) maneja toda la navegación en todos los breakpoints.

## What Changes

- `frontend/src/shared/components/Navbar.tsx` — eliminar `useNavLinks` import, hook call, y el bloque `navLinks.map(...)`. El Navbar queda exclusivamente con: hamburger (que abre el Sidebar) + brand + user email + logout + theme toggle.

No se modifica el Sidebar ni `useNavLinks`. No se crean páginas ni rutas nuevas.

## Capabilities

### New Capabilities
_(ninguna — solo corrección de comportamiento existente)_

### Modified Capabilities
- `role-based-navigation`: el Navbar deja de renderizar links de navegación. El Sidebar pasa a ser el único punto de navegación en todos los breakpoints.

## Impact

- Un solo archivo modificado: `frontend/src/shared/components/Navbar.tsx`
- Sin cambios de API, stores, hooks ni rutas
- Sin tests de Navbar existentes — sin riesgo de regresión de tests
- Tests de `useNavLinks` siguen intactos (el hook no cambia)
