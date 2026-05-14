## Context

El backend de direcciones (`addresses-crud-by-user`, archivado 2026-05-14) expone 6 endpoints REST en `/api/v1/direcciones`. Este change implementa la UI completa siguiendo FSD estricto (`Pages → Widgets → Features → Entities → Shared`). El proyecto ya tiene infraestructura de TanStack Query v5, Axios con interceptor JWT, Tailwind v4 con tokens semánticos, uiStore para toasts, y componentes primitivos (Card, Button, Input, Modal, Skeleton, Badge) en `shared/components/`.

## Goals / Non-Goals

**Goals:**
- Página `/direcciones` funcional para usuarios CLIENT autenticados
- CRUD completo de direcciones conectado al backend real
- UX con feedback visual (skeletons, toasts, confirmación de eliminación)
- Tests vitest ≥ 40% coverage en componentes y hooks nuevos
- Tests E2E Playwright para flujo CRUD autenticado

**Non-Goals:**
- Integración con checkout (eso pertenece a `frontend-payment-checkout-ui`)
- Selección de dirección durante pedido
- Gestión de direcciones para otros usuarios (solo el propio CLIENT)

## Decisions

### D1: TanStack Query v5 para todo estado servidor — sin Zustand

Las direcciones son datos del servidor. Se gestionan exclusivamente con TanStack Query v5. No se duplican en Zustand. Invalidación de cache tras cada mutación con `queryClient.invalidateQueries({ queryKey: ['addresses'] })`.

**Alternativa descartada**: guardar lista en Zustand como cache local. Descartada porque introduce duplicación y viola la separación de estado del proyecto.

### D2: Formulario con estado React local (useState) — sin TanStack Form

`@tanstack/react-form` no está instalado. El formulario `AddressForm` usa `useState` para los campos y validación client-side básica (required + longitudes). La validación de negocio definitiva la hace el backend.

**Alternativa descartada**: instalar TanStack Form ahora. Se postergó al change de formularios según AGENTS.md.

### D3: AddressForm como modal usando el componente Modal primitivo existente

El formulario de crear/editar se presenta en el componente `Modal` ya disponible en `shared/components/`. Se reutiliza para modo crear (sin `initialData`) y modo editar (con `initialData: DireccionResponse`). Un único componente, dos modos.

### D4: Confirmación de eliminación con window.confirm nativo

Para eliminar se usa `window.confirm` nativo en lugar de un modal custom. Esto simplifica la implementación y es suficiente para la UX esperada. Si el diseño final requiere modal, se puede refactorizar en un change posterior.

### D5: Estructura de hooks — un archivo por operación

Cada operación tiene su propio hook file en `features/addresses/hooks/`:
- `useAddresses.ts` — GET lista
- `useCreateAddress.ts` — POST
- `useUpdateAddress.ts` — PUT
- `useSetPredeterminada.ts` — PATCH
- `useDeleteAddress.ts` — DELETE

Esto facilita el testing individual y sigue el patrón ya establecido en `features/products/hooks/`.

## Risks / Trade-offs

- **Cache staleness tras mutación** → Mitigación: `invalidateQueries` en `onSuccess` de cada mutation para refetch inmediato.
- **Carrera condición en PATCH predeterminada** → Mitigación: el backend garantiza consistencia (RN-DI02); el frontend solo refetch tras respuesta.
- **Modal accesible** → El componente Modal existente ya usa `<dialog>` nativo con `aria-modal` y focus trap.

## Migration Plan

1. Crear `frontend/src/features/addresses/` con tipos, hooks y componentes
2. Crear `frontend/src/pages/MyAddressesPage.tsx`
3. Registrar ruta `/direcciones` en `Router.tsx` dentro del grupo CLIENT
4. Verificar que el link "Mis Direcciones" en el Sidebar ya existe (implementado en `frontend-navigation-by-role`)
5. No hay migraciones de BD ni cambios en backend

## Open Questions

- ¿El link "Mis Direcciones" en el Sidebar apunta a `/direcciones`? Verificar al implementar en `frontend/src/shared/routing/` o `features/navigation/`.
