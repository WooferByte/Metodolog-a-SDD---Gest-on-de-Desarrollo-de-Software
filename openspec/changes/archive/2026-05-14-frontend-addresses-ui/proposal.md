## Why

Los usuarios CLIENT necesitan gestionar sus direcciones de entrega directamente desde el frontend. El backend `addresses-crud-by-user` ya está implementado y archivado (2026-05-14); este change cierra el gap de UI que queda pendiente para habilitar el flujo completo de checkout.

## What Changes

- Nueva página `MyAddressesPage` en `/direcciones` (ruta protegida CLIENT)
- Nuevo feature FSD `frontend/src/features/addresses/` con componentes, hooks y tipos
- 5 hooks TanStack Query v5 para las 6 operaciones REST del backend de direcciones
- Componente `AddressCard` con acciones editar / eliminar / marcar predeterminada
- Componente `AddressForm` reutilizable para crear y editar (modal inline)
- Estado vacío, skeletons de carga y confirmación de eliminación
- Toasts de éxito/error en cada mutación (vía `uiStore` existente)
- Tests vitest para hooks y componentes
- Tests E2E Playwright para el flujo CRUD completo autenticado como CLIENT

## Capabilities

### New Capabilities

- `address-management-ui`: Página y feature FSD completo para gestión de direcciones de entrega por usuario CLIENT autenticado. Incluye listado, creación, edición, eliminación y marcado de predeterminada.

### Modified Capabilities

<!-- Ninguna — no se modifican specs de backend ni contratos de API existentes -->

## Impact

- **Frontend**: `frontend/src/pages/MyAddressesPage.tsx` (nueva), `frontend/src/features/addresses/` (nuevo feature FSD)
- **Router**: agregar ruta `/direcciones` protegida para rol CLIENT en `frontend/src/app/Router.tsx`
- **API**: consume endpoints ya existentes en `/api/v1/direcciones`
- **Dependencias nuevas**: ninguna — usa stack ya instalado (TanStack Query v5, Axios, Tailwind v4, lucide-react)
- **Sin cambios en backend**: solo integración frontend con endpoints existentes
