## 0. Skills

- [ ] 0.1 Leer `.agents/skills/tailwind-design-system/SKILL.md` — componentes React con Tailwind v4, tokens semánticos OKLCH, solo tokens semánticos (sin colores crudos)
- [ ] 0.2 Leer `.agents/skills/ui-design-system/SKILL.md` — WCAG AA, ARIA, componentes accesibles, three-tier token system
- [ ] 0.3 Leer `.agents/skills/frontend-state-management/SKILL.md` — separación TanStack Query v5 (estado servidor) vs Zustand v5 (estado cliente), evitar duplicación
- [ ] 0.4 Leer `.agents/skills/vercel-react-best-practices/SKILL.md` — performance React, code splitting, React.lazy, TanStack Query cache patterns, invalidateQueries
- [ ] 0.5 Leer `.agents/skills/testing-e2e-playwright/SKILL.md` — auth JWT vía localStorage, loginAs() helper, mocks FastAPI con page.route, guards de ruta

---

## 1. Tipos TypeScript

- [ ] 1.1 Crear `frontend/src/features/addresses/types/index.ts` con interfaces:
  - `DireccionResponse` — todos los campos del backend: `id, usuario_id, alias, linea1, piso?, departamento?, ciudad, codigo_postal, referencia?, es_predeterminada, creado_en, actualizado_en`
  - `DireccionCreate` — campos obligatorios para POST: `alias, linea1, ciudad, codigo_postal` + opcionales: `piso?, departamento?, referencia?`
  - `DireccionUpdate` — mismos campos que DireccionCreate (todos opcionales para PATCH/PUT parcial)
  - `AddressFormData` — tipo para el estado del formulario React (igual a DireccionCreate pero todos string para controlled inputs)

---

## 2. Hooks TanStack Query v5

- [ ] 2.1 Crear `frontend/src/features/addresses/hooks/useAddresses.ts`
  - `useQuery` con `queryKey: ['addresses']`
  - GET `/api/v1/direcciones`
  - Retorna `{ data: DireccionResponse[], isLoading, error }`

- [ ] 2.2 Crear `frontend/src/features/addresses/hooks/useCreateAddress.ts`
  - `useMutation` con POST a `/api/v1/direcciones`
  - `onSuccess`: `queryClient.invalidateQueries({ queryKey: ['addresses'] })` + toast éxito via `uiStore.addToast`
  - Body: `DireccionCreate`

- [ ] 2.3 Crear `frontend/src/features/addresses/hooks/useUpdateAddress.ts`
  - `useMutation` con PUT a `/api/v1/direcciones/{id}`
  - `onSuccess`: invalidar `['addresses']` + toast éxito
  - Variables: `{ id: number; data: DireccionUpdate }`

- [ ] 2.4 Crear `frontend/src/features/addresses/hooks/useSetPredeterminada.ts`
  - `useMutation` con PATCH a `/api/v1/direcciones/{id}/predeterminada`
  - Sin body (el backend no requiere body)
  - `onSuccess`: invalidar `['addresses']` + toast éxito "Dirección predeterminada actualizada"
  - Variables: `{ id: number }`

- [ ] 2.5 Crear `frontend/src/features/addresses/hooks/useDeleteAddress.ts`
  - `useMutation` con DELETE a `/api/v1/direcciones/{id}`
  - `onSuccess`: invalidar `['addresses']` + toast éxito "Dirección eliminada"
  - Variables: `{ id: number }`

---

## 3. Componente AddressCard

- [ ] 3.1 Crear `frontend/src/features/addresses/components/AddressCard.tsx`
  - Props: `address: DireccionResponse`, `onEdit: () => void`, `onDelete: () => void`, `onSetPredeterminada: () => void`
  - Mostrar: alias (heading), linea1, piso+departamento (si existen), ciudad, codigo_postal, referencia (si existe)
  - Badge "Predeterminada" (variante success/accent) cuando `es_predeterminada === true`
  - Botón "Editar" — siempre visible
  - Botón "Eliminar" — siempre visible
  - Botón "Marcar predeterminada" — OCULTO cuando `es_predeterminada === true`
  - Solo tokens semánticos Tailwind v4 (bg-card, text-foreground, border-border, etc.)
  - ARIA: `article` con `aria-label={address.alias}`, botones con `aria-label` descriptivos

---

## 4. Componente AddressForm

- [ ] 4.1 Crear `frontend/src/features/addresses/components/AddressForm.tsx`
  - Props: `initialData?: DireccionResponse`, `onSubmit: (data: DireccionCreate) => void`, `onCancel: () => void`, `isLoading?: boolean`
  - Estado interno con `useState<AddressFormData>` para cada campo
  - Cuando `initialData` está presente: pre-llenar campos (modo editar)
  - Cuando `initialData` es undefined: campos vacíos (modo crear)
  - Campos con `<label>` asociado por `htmlFor/id`
  - Validación client-side antes de `onSubmit`:
    - `alias`: requerido, max 100 chars
    - `linea1`: requerido, max 200 chars
    - `ciudad`: requerido, max 100 chars
    - `codigo_postal`: requerido, max 20 chars
    - `piso`, `departamento`, `referencia`: opcionales, max razonable
  - Mostrar mensajes de error inline bajo cada campo con `role="alert"`
  - Botones: "Cancelar" (llama `onCancel`) y "Guardar" (submit, disabled cuando `isLoading`)
  - Spinner o texto "Guardando..." en botón cuando `isLoading === true`
  - Solo tokens semánticos Tailwind v4
  - ARIA: `aria-invalid` en inputs con error, `aria-describedby` apuntando al mensaje de error

---

## 5. Página MyAddressesPage

- [ ] 5.1 Crear `frontend/src/pages/MyAddressesPage.tsx`
  - Usar `useAddresses()` para obtener la lista
  - Estado de carga: mostrar 3 `Skeleton` de la forma de una AddressCard
  - Estado error: mostrar mensaje de error (el toast ya lo muestra el interceptor)
  - Estado vacío (data?.length === 0): mostrar mensaje "No tenés direcciones guardadas" + botón "Agregar dirección"
  - Estado con datos: grid/lista de `AddressCard`
  - Botón "Agregar dirección" en la parte superior de la página
  - Estado local para controlar modal:
    - `modalOpen: boolean`
    - `editingAddress: DireccionResponse | null`
  - Al presionar "Agregar": abrir modal con `editingAddress = null`
  - Al presionar "Editar" en un card: abrir modal con `editingAddress = address`
  - `AddressForm` dentro de componente `Modal` (existente en shared/components)
  - `onSubmit` del formulario llama `createAddress.mutate()` o `updateAddress.mutate()` según `editingAddress`
  - `onDelete`: llamar `window.confirm('¿Eliminás esta dirección?')` y si confirma: `deleteAddress.mutate({ id })`
  - `onSetPredeterminada`: llamar `setPredeterminada.mutate({ id })`
  - Heading `<h1>Mis Direcciones</h1>` visible
  - Solo tokens semánticos, responsive (grid 1 col mobile, 2 col md+)

- [ ] 5.2 Registrar ruta en `frontend/src/app/Router.tsx`
  - Agregar `/direcciones` dentro del bloque de rutas protegidas para rol CLIENT
  - Usar `React.lazy(() => import('@/pages/MyAddressesPage'))` para code splitting
  - Wrappear con `Suspense` (ya debe existir el patrón en Router.tsx)

---

## 6. Tests Vitest

- [ ] 6.1 Crear `frontend/src/features/addresses/__tests__/AddressCard.test.tsx`
  - Test: renderiza alias, linea1, ciudad, codigo_postal
  - Test: muestra Badge "Predeterminada" cuando `es_predeterminada === true`
  - Test: NO muestra Badge cuando `es_predeterminada === false`
  - Test: botón "Marcar predeterminada" visible cuando `es_predeterminada === false`
  - Test: botón "Marcar predeterminada" NO visible cuando `es_predeterminada === true`
  - Test: llama `onEdit` al presionar "Editar"
  - Test: llama `onDelete` al presionar "Eliminar"
  - Test: llama `onSetPredeterminada` al presionar "Marcar predeterminada"

- [ ] 6.2 Crear `frontend/src/features/addresses/__tests__/AddressForm.test.tsx`
  - Test: renderiza todos los campos
  - Test: pre-llena campos cuando recibe `initialData`
  - Test: campos vacíos cuando no recibe `initialData`
  - Test: muestra error de validación cuando `alias` está vacío y se hace submit
  - Test: llama `onSubmit` con datos correctos cuando validación pasa
  - Test: botón "Guardar" disabled cuando `isLoading === true`
  - Test: llama `onCancel` al presionar "Cancelar"

- [ ] 6.3 Crear `frontend/src/features/addresses/__tests__/useAddresses.test.ts`
  - Setup con `QueryClientProvider` de test
  - Test: retorna lista de direcciones en estado success
  - Test: `isLoading` verdadero durante fetch
  - Mock de axios con `vi.mock`

---

## 7. Tests E2E Playwright

- [ ] 7.1 Crear `frontend/e2e/addresses/addresses.spec.ts`
  - Helper `loginAs(page, 'CLIENT')` del helper existente en `e2e/helpers/auth.ts`
  - Test: CLIENT accede a `/direcciones` — página visible, heading "Mis Direcciones"
  - Test: sin sesión → `/direcciones` redirige a `/login`
  - Test: estado vacío — mock GET devuelve `[]`, se muestra mensaje vacío
  - Test: listado con datos — mock GET devuelve 2 direcciones, se muestran 2 cards
  - Test: crear dirección — mock POST exitoso, formulario se cierra, aparece toast
  - Test: Badge "Predeterminada" visible en la dirección con `es_predeterminada: true`
  - Usar `page.route('**/api/v1/direcciones**', ...)` para mockear todas las operaciones sin backend real

---

## 8. Verificación final

- [ ] 8.1 Correr `npx vitest run --reporter=verbose` desde `frontend/` — 0 fallos
- [ ] 8.2 Correr `npx tsc --noEmit` desde `frontend/` — 0 errores TypeScript
- [ ] 8.3 Verificar que la ruta `/direcciones` está protegida (redirect a `/login` sin sesión)
- [ ] 8.4 Verificar que el link "Mis Direcciones" en el Sidebar apunta a `/direcciones`
- [ ] 8.5 Leer `.agents/skills/post-change-verification/SKILL.md` y ejecutar el health check completo
