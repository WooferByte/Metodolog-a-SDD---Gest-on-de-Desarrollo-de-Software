## 0. Skills

- [x] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — componentes con Tailwind v4, tokens @theme, patrones CVA
- [x] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — accesibilidad WCAG, ARIA, design tokens, patrones Radix/shadcn
- [x] 0.3 Leer `.agents/skills/vercel-react-best-practices/AGENTS.md` — performance React, code splitting, TanStack Query cache
- [x] 0.4 Leer `.agents/skills/frontend-state-management/SKILL.md` — Zustand vs TanStack Query, evitar duplicación de estado

## 1. Tipos y contratos

- [x] 1.1 Crear `src/shared/types/api.ts` con el tipo `ApiError` que modela RFC 7807: `{ type: string; title: string; status: number; detail?: string; instance?: string }`
- [x] 1.2 Exportar `ApiError` desde `src/shared/types/index.ts` (crear el archivo si no existe) para uso centralizado con path alias `@/shared/types`

## 2. Error Boundary global — refactor a Tailwind v4

- [x] 2.1 Abrir `src/app/ErrorBoundary.tsx` — leer el código actual antes de modificar
- [x] 2.2 Reemplazar todos los estilos `style={{...}}` inline por clases Tailwind v4 equivalentes (usar tokens `bg-background`, `text-foreground`, `text-destructive`, `rounded-lg`, `shadow-sm`, etc.)
- [x] 2.3 Agregar botón "Ir al inicio" con `<a href="/">` además del botón "Recargar Página"
- [x] 2.4 Asegurar que en modo `development` se muestra stack trace y en `production` solo el mensaje genérico
- [x] 2.5 Verificar que la interfaz `Props` y `State` permanecen sin cambios (no romper contrato externo)

## 3. Componente ToastContainer

- [x] 3.1 Crear `src/shared/components/ToastContainer.tsx` — componente funcional que consume `useUIStore((s) => s.toasts)` y `useUIStore((s) => s.removeToast)`
- [x] 3.2 Implementar lógica de auto-dismiss con `useEffect` + `setTimeout`: `success`/`info` → 4000ms, `warning` → 5000ms, `error` → 6000ms; respetar `toast.duration` si está definido
- [x] 3.3 Implementar botón X de cierre manual que llama `removeToast(toast.id)`
- [x] 3.4 Estilizar cada tipo de toast con color semántico Tailwind v4: `success` → verde, `error` → rojo/destructive, `warning` → amarillo/naranja, `info` → azul
- [x] 3.5 Agregar íconos de lucide-react apropiados: `CheckCircle2` (success), `XCircle` (error), `AlertTriangle` (warning), `Info` (info)
- [x] 3.6 Posicionar el contenedor con `fixed bottom-4 right-4 z-50 flex flex-col gap-2` para que no bloquee contenido de la app
- [x] 3.7 Implementar límite de 5 toasts simultáneos: si se supera, el más antiguo es eliminado (hacerlo en `addToast` del store o en el componente antes del render)

## 4. Interceptor Axios — mapeo de status codes

- [x] 4.1 Abrir `src/shared/api/axios.ts` — leer el código completo antes de modificar
- [x] 4.2 Crear función helper `getErrorMessage(status: number, detail?: string): { message: string; type: Toast['type'] }` con el mapeo documentado en design.md (400/403/404/422/429/500/otros)
- [x] 4.3 En el bloque `if (status !== 401) { return Promise.reject(error) }`: antes del reject, llamar `useUIStore.getState().addToast(...)` con el mensaje mapeado
- [x] 4.4 Agregar manejo para errores de red (sin `error.response`): mostrar toast "Sin conexión. Verificá tu red." con tipo `error`
- [x] 4.5 Asegurar que el flujo de refresh 401 NO es modificado — solo agregar lógica para status ≠ 401 y sin respuesta
- [x] 4.6 Importar `useUIStore` al inicio del archivo (ya se importa `useAuthStore` — misma carpeta `@/store`)

## 5. Integración en App.tsx

- [x] 5.1 Abrir `src/app/App.tsx` — leer el código actual antes de modificar
- [x] 5.2 Importar `ToastContainer` desde `@/shared/components/ToastContainer`
- [x] 5.3 Montar `<ToastContainer />` dentro de `<BrowserRouter>` y después de `<Router />` para que sea visible globalmente y tenga acceso al contexto de routing si fuera necesario

## 6. Tests

- [x] 6.1 Crear `src/app/__tests__/ErrorBoundary.test.tsx` — test: renderizado normal (sin error renderiza children), fallback UI (simular error con `render` + error en child), botón Recargar llama `window.location.reload`
- [x] 6.2 Crear `src/shared/components/__tests__/ToastContainer.test.tsx` — test: sin toasts no renderiza nada, toast visible al agregar al store, botón X llama `removeToast`, auto-dismiss dispara `removeToast` tras el timeout (usar `vi.useFakeTimers()`)
- [x] 6.3 Crear o extender `src/shared/api/__tests__/axios.test.ts` — test: status 400 despacha `addToast` con tipo `warning`, status 403 con tipo `error`, status 500 con tipo `error`, error de red (sin respuesta) despacha `addToast` con "Sin conexión"
- [x] 6.4 Ejecutar `npx vitest run` — verificar que todos los tests pasan y cobertura de los módulos nuevos ≥ 40%

## 7. Verificación y lint

- [x] 7.1 Ejecutar `npm run lint` — corregir cualquier warning de TypeScript o ESLint
- [x] 7.2 Verificar manualmente en browser: disparar un error de renderizado (comentar un componente que tire) → confirmar fallback UI de ErrorBoundary se ve correctamente
- [x] 7.3 Verificar manualmente: llamar un endpoint inexistente desde DevTools o un componente temporal → confirmar que aparece toast de error en la esquina inferior derecha
- [x] 7.4 Verificar que el toast desaparece automáticamente y que el botón X lo cierra manualmente
