## 1. Lectura de contexto

- [x] 1.1 Leer `.agents/skills/tailwind-design-system/SKILL.md`
- [x] 1.2 Leer `.agents/skills/ui-design-system/SKILL.md`
- [x] 1.3 Leer `.agents/skills/zustand-state-management/README.md`
- [x] 1.4 Leer `frontend/src/store/authStore.ts` — entender `hasRole`, `user.roles`, `isAuthenticated`, `_hasHydrated`
- [x] 1.5 Leer `frontend/src/store/types.ts` — entender el tipo `AuthStore` y `User`
- [x] 1.6 Leer `frontend/src/shared/hooks/useLogout.ts` — para reusar en Navbar
- [x] 1.7 Leer `frontend/src/shared/components/Navbar.tsx` — estado actual a reemplazar

## 2. Hook useNavLinks

- [x] 2.1 Crear `frontend/src/shared/hooks/useNavLinks.ts`
- [x] 2.2 Definir tipo `NavLink = { label: string; to: string }`
- [x] 2.3 Implementar lógica de prioridad de roles: ADMIN → PEDIDOS → STOCK → CLIENT → unauthenticated
- [x] 2.4 Retornar links según estado: unauthenticated (3), CLIENT (5), STOCK (3), PEDIDOS (1), ADMIN (6)
- [x] 2.5 Guardar `_hasHydrated` guard: devolver links públicos hasta que hydration complete

## 3. Tests del hook

- [x] 3.1 Crear `frontend/src/shared/hooks/__tests__/useNavLinks.test.ts`
- [x] 3.2 Test: usuario null → 3 links públicos (Catálogo, Iniciar sesión, Registrarse)
- [x] 3.3 Test: roles `["CLIENT"]` → 5 links cliente
- [x] 3.4 Test: roles `["STOCK"]` → 3 links stock
- [x] 3.5 Test: roles `["PEDIDOS"]` → 1 link panel pedidos
- [x] 3.6 Test: roles `["ADMIN"]` → 6 links admin
- [x] 3.7 Ejecutar `cd frontend && npx vitest run src/shared/hooks/__tests__/useNavLinks.test.ts` — todos verdes

## 4. Reescribir Navbar

- [x] 4.1 Reemplazar `frontend/src/shared/components/Navbar.tsx` completo
- [x] 4.2 Usar Tailwind v4 utility classes exclusivamente — cero `style={{}}` props
- [x] 4.3 Usar `useNavLinks()` para obtener los links dinámicos
- [x] 4.4 Mapear los links con `<Link>` de react-router-dom
- [x] 4.5 Mostrar logout button cuando `isAuthenticated === true` (usando `useLogout`)
- [x] 4.6 Mostrar nombre/email del usuario autenticado junto al logout
- [x] 4.7 Aplicar `_hasHydrated` guard: mostrar links públicos mientras hidrata

## 5. Validación

- [x] 5.1 Ejecutar `cd frontend && npx vitest run` — sin regresiones
- [x] 5.2 Ejecutar `cd frontend && npx tsc --noEmit` — sin errores de tipos
- [x] 5.3 Verificar que todos los imports usan `@/` (no rutas relativas `../`)
