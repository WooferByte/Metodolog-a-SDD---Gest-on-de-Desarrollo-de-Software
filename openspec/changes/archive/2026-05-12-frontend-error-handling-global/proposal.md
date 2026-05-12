## Why

El frontend carece de un sistema unificado de manejo de errores: el interceptor Axios no mapea los status codes a mensajes legibles para el usuario, no existe un mecanismo global para mostrar toasts de error ni un Error Boundary con visual Tailwind v4, y los errores RFC 7807 del backend (ya implementados) se pierden en la UI. Esto deja al usuario sin feedback claro ante fallos de red, 403, 429 y 500.

## What Changes

- **Error Boundary global mejorado**: refactorizar `src/app/ErrorBoundary.tsx` para usar Tailwind v4 en lugar de estilos inline, integrar botón de "Reintentar" con reset de state, y respetar el design system del proyecto.
- **Interceptor Axios extendido**: ampliar `src/shared/api/axios.ts` con un segundo tramo del interceptor de respuesta que mapea status codes (400 → "Datos inválidos", 403 → "Sin permiso", 404 → "No encontrado", 429 → "Demasiadas solicitudes, esperá un momento", 500 → "Error del servidor, intentá más tarde") a mensajes legibles y despacha toasts vía `useUIStore.addToast`.
- **Componente `<ToastContainer>`**: nuevo componente `src/shared/components/ToastContainer.tsx` que consume `useUIStore.toasts` y renderiza las notificaciones con animaciones Tailwind v4 y auto-dismiss configurable.
- **Integración en `App.tsx`**: montar `<ToastContainer>` dentro del árbol de providers, visible globalmente.
- **Tipos RFC 7807**: declarar tipo `ApiError` que mapea `{ type, title, status, detail, instance }` para tipado estricto en el interceptor.
- **Tests**: tests vitest para el interceptor (mapeo de status codes), para `ToastContainer` (render, dismiss, auto-dismiss), y para el Error Boundary (render del fallback).

## Capabilities

### New Capabilities

- `global-error-handling`: Sistema centralizado de captura y presentación de errores HTTP y de renderizado. Incluye Error Boundary global con Tailwind v4, interceptor Axios con mapeo de status codes RFC 7807, y ToastContainer de notificaciones efímeras.

### Modified Capabilities

- `axios-interceptor`: El interceptor existente en `src/shared/api/axios.ts` extiende su tramo de error para incorporar mapeo de status codes a mensajes y despacho a uiStore. El comportamiento de refresh de tokens (401) no cambia.

## Impact

- **Archivos modificados**: `src/app/ErrorBoundary.tsx`, `src/shared/api/axios.ts`, `src/app/App.tsx`
- **Archivos nuevos**: `src/shared/components/ToastContainer.tsx`, `src/shared/types/api.ts`
- **Dependencias existentes usadas**: Zustand v5 (`useUIStore.addToast`/`removeToast`), Tailwind v4, lucide-react (iconos de toast), React 18 class component (Error Boundary)
- **Sin dependencias nuevas a instalar**
- **Dependencia upstream**: `backend-error-handling-rfc7807` (backend ya devuelve RFC 7807 — este change consume ese contrato)
- **Afecta**: todos los cambios futuros de UI que generen errores HTTP se benefician automáticamente del sistema de toasts
