## 0. Skills

- [x] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — tokens @theme Tailwind v4, dark mode variant, componentes con CVA
- [x] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — accesibilidad WCAG AA, patrones Radix/compound components, OKLCH
- [x] 0.3 Leer `.agents/skills/vercel-react-best-practices/AGENTS.md` — performance React, code splitting, TanStack Query cache
- [x] 0.4 Leer `.agents/skills/zustand-state-management/README.md` — Zustand v5 TypeScript patterns, selectores granulares

## 1. Dependencias y utilidades base

- [x] 1.1 Instalar `clsx` y `tailwind-merge` en `frontend/`: `npm install clsx tailwind-merge`
- [x] 1.2 Crear `frontend/src/shared/lib/utils.ts` con la función `cn()` usando `clsx` + `tailwind-merge`
- [x] 1.3 Verificar que `frontend/src/index.css` importa Tailwind v4 con `@import "tailwindcss"`

## 2. Design tokens — Tailwind v4 @theme

- [x] 2.1 Agregar bloque `@theme {}` en `frontend/src/index.css` con todos los tokens semánticos de color en OKLCH (`--color-background`, `--color-foreground`, `--color-primary`, `--color-primary-foreground`, `--color-secondary`, `--color-secondary-foreground`, `--color-muted`, `--color-muted-foreground`, `--color-accent`, `--color-accent-foreground`, `--color-destructive`, `--color-destructive-foreground`, `--color-border`, `--color-ring`, `--color-card`, `--color-card-foreground`)
- [x] 2.2 Agregar tokens de radio (`--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`) al bloque `@theme {}`
- [x] 2.3 Agregar tokens de animación (`--animate-fade-in`, `--animate-fade-out`, `--animate-slide-in`) con `@keyframes` dentro de `@theme {}`
- [x] 2.4 Agregar `@custom-variant dark (&:where(.dark, .dark *))` en `index.css`
- [x] 2.5 Agregar bloque `.dark {}` en `index.css` con los overrides OKLCH para todos los tokens de color

## 3. Componentes atómicos — shared/components/ui/

- [x] 3.1 Crear `frontend/src/shared/components/ui/Button.tsx` — variantes: `primary`, `secondary`, `outline`, `ghost`, `destructive`; tamaños: `sm`, `md`, `lg`; props: `loading`, `disabled`; usa `cn()`
- [x] 3.2 Crear `frontend/src/shared/components/ui/Input.tsx` — props: `label`, `error`, `id`, `type`; incluye `<label>`, `aria-invalid`, `role="alert"` en error; usa `cn()`
- [x] 3.3 Crear `frontend/src/shared/components/ui/Card.tsx` — compound: `Card`, `CardHeader`, `CardContent`, `CardFooter`; cada uno acepta `className`; usa `cn()`
- [x] 3.4 Crear `frontend/src/shared/components/ui/Modal.tsx` — usa `<dialog>` nativo con `showModal()`/`close()`; props: `isOpen`, `onClose`, `title`, `children`; trap de foco; cierra con Escape y click en backdrop
- [x] 3.5 Crear `frontend/src/shared/components/ui/Badge.tsx` — variantes: `default`, `success`, `warning`, `error`, `info`; usa tokens semánticos; usa `cn()`
- [x] 3.6 Crear `frontend/src/shared/components/ui/Skeleton.tsx` — prop `variant`: `text`, `circle`, `rect`; `animate-pulse`; acepta `className`; usa `cn()`
- [x] 3.7 Crear `frontend/src/shared/components/ui/index.ts` — barrel export de todos los componentes UI

## 4. Componentes de layout — shared/components/layout/

- [x] 4.1 Crear `frontend/src/shared/components/layout/Footer.tsx` — `<footer>` con copyright "© 2026 Food Store"; Tailwind v4 semántico
- [x] 4.2 Crear `frontend/src/shared/components/layout/Sidebar.tsx` — usa `useNavLinks()` para links role-aware; se muestra/oculta con `uiStore.sidebarOpen`; overlay en mobile (`< lg`), panel persistente en `lg+`; cierra con Escape en mobile; backdrop con click-to-close en mobile
- [x] 4.3 Crear `frontend/src/shared/components/layout/AppLayout.tsx` — wrapper con `<Navbar>`, `<Sidebar>`, `<main id="main-content">`, `<Footer>`; acepta `children`; layout responsive (flex-col o flex-row según sidebar)
- [x] 4.4 Crear `frontend/src/shared/components/layout/index.ts` — barrel export de layout components

## 5. Extensión de Navbar existente

- [x] 5.1 Modificar `frontend/src/shared/components/Navbar.tsx` — agregar botón hamburger (izquierda) que llama `uiStore.toggleSidebar`; `aria-label` dinámico según `sidebarOpen` ("Abrir menú" / "Cerrar menú"); icono `Menu`/`X` de `lucide-react`
- [x] 5.2 Modificar `frontend/src/shared/components/Navbar.tsx` — agregar botón theme-toggle (derecha, junto a logout); alterna entre `Moon`/`Sun` de `lucide-react`; llama `uiStore.setTheme('dark' | 'light')`
- [x] 5.3 Verificar que todos los tests existentes de Navbar siguen pasando tras las modificaciones

## 6. Actualización de App.tsx — layout shell y dark mode

- [x] 6.1 Modificar `frontend/src/app/App.tsx` — reemplazar `<Navbar />` + `<Router />` con `<AppLayout><Router /></AppLayout>`
- [x] 6.2 Agregar `useEffect` en `App.tsx` que suscribe a `useUIStore((s) => s.theme)` y aplica/quita clase `dark` en `document.documentElement`
- [x] 6.3 Verificar que `<ToastContainer />` sigue renderizando fuera de `<main>` (dentro de `<AppLayout>` o directamente en `App.tsx`)

## 7. Tests

- [x] 7.1 Crear `frontend/src/shared/components/ui/__tests__/Button.test.tsx` — testear: render default, variante destructive, loading state desactiva botón, className override
- [x] 7.2 Crear `frontend/src/shared/components/ui/__tests__/Input.test.tsx` — testear: render con label, error muestra mensaje + aria-invalid, type password
- [x] 7.3 Crear `frontend/src/shared/components/ui/__tests__/Card.test.tsx` — testear: render compound completo, className override
- [x] 7.4 Crear `frontend/src/shared/components/ui/__tests__/Badge.test.tsx` — testear: variantes success y error
- [x] 7.5 Crear `frontend/src/shared/components/ui/__tests__/Skeleton.test.tsx` — testear: variant circle tiene `rounded-full`, animate-pulse presente
- [x] 7.6 Crear `frontend/src/shared/components/ui/__tests__/Modal.test.tsx` — testear: isOpen=true muestra contenido, isOpen=false oculta, Escape llama onClose
- [x] 7.7 Crear `frontend/src/shared/lib/__tests__/utils.test.ts` — testear: cn() merge no-conflictivo, resolución de clases conflictivas
- [x] 7.8 Crear `frontend/src/shared/components/layout/__tests__/Sidebar.test.tsx` — testear: renderiza links, oculto cuando sidebarOpen=false
- [x] 7.9 Crear `frontend/src/shared/components/layout/__tests__/Footer.test.tsx` — testear: texto copyright presente, tag `<footer>`

## 8. Verificación final

- [x] 8.1 Ejecutar `npx vitest run` — todos los tests deben pasar (incluye tests preexistentes)
- [x] 8.2 Ejecutar `npm run lint` — sin errores de TypeScript ni ESLint
- [x] 8.3 Smoke test manual: abrir `http://localhost:5173`, verificar: Navbar con hamburger + tema, sidebar abre/cierra, dark mode activa, todas las rutas renderizan, Footer visible
- [x] 8.4 Verificar cobertura de tests frontend ≥ 40% (`npx vitest run --coverage`)
