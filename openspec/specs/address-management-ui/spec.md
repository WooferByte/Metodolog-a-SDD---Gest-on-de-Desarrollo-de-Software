## Capability: address-management-ui
Página y feature FSD para gestión de direcciones de entrega por usuarios CLIENT autenticados.

---

#### REQ-AM-UI-01: Página /direcciones protegida para CLIENT

La ruta `/direcciones` DEBE estar registrada en `Router.tsx` dentro del grupo de rutas protegidas para rol CLIENT. Usuarios no autenticados son redirigidos a `/login`. Usuarios con rol insuficiente son redirigidos a `/403`.

#### Scenario: CLIENT accede a /direcciones
- **Given** usuario autenticado con rol CLIENT
- **When** navega a `/direcciones`
- **Then** ve la página `MyAddressesPage` con su listado de direcciones

#### Scenario: usuario no autenticado accede a /direcciones
- **Given** usuario sin sesión activa
- **When** navega a `/direcciones`
- **Then** es redirigido a `/login`

---

#### REQ-AM-UI-02: Listado de direcciones con AddressCard

La página DEBE mostrar una lista de `AddressCard` con la información de cada dirección del usuario. Durante la carga inicial se muestran skeletons. Si no hay direcciones, se muestra estado vacío con mensaje y botón "Agregar dirección".

#### Scenario: usuario con direcciones registradas
- **Given** usuario CLIENT con 3 direcciones en backend
- **When** carga la página `/direcciones`
- **Then** se muestran 3 `AddressCard`, cada una con alias, linea1, ciudad, codigo_postal
- **And** la dirección con `es_predeterminada=true` muestra Badge "Predeterminada"

#### Scenario: usuario sin direcciones
- **Given** usuario CLIENT sin direcciones registradas
- **When** carga la página `/direcciones`
- **Then** se muestra estado vacío con mensaje "No tenés direcciones guardadas"
- **And** se muestra botón "Agregar dirección"

#### Scenario: carga inicial
- **Given** usuario CLIENT en `/direcciones`
- **When** la query de direcciones está en estado loading
- **Then** se muestran skeletons en lugar de AddressCard

---

#### REQ-AM-UI-03: Crear dirección

El formulario `AddressForm` en modo crear DEBE validar los campos obligatorios antes de enviar. Al confirmar se hace POST al backend. En éxito: cierra el formulario, invalida el cache de direcciones, y muestra toast de éxito.

Campos obligatorios: `alias`, `linea1`, `ciudad`, `codigo_postal`.
Campos opcionales: `piso`, `departamento`, `referencia`.

#### Scenario: crear dirección válida
- **Given** usuario en `/direcciones`, formulario abierto en modo crear
- **When** completa todos los campos obligatorios y presiona "Guardar"
- **Then** se hace POST a `/api/v1/direcciones`
- **And** el formulario se cierra
- **And** aparece toast de éxito "Dirección guardada"
- **And** la nueva dirección aparece en el listado

#### Scenario: intentar crear sin campos obligatorios
- **Given** formulario de creación abierto
- **When** presiona "Guardar" sin completar `alias`
- **Then** se muestra mensaje de validación "El alias es obligatorio"
- **And** NO se hace la request al backend

---

#### REQ-AM-UI-04: Editar dirección

El botón "Editar" en cada `AddressCard` abre `AddressForm` en modo editar con los datos actuales pre-llenados. Al confirmar se hace PUT al backend. En éxito: cierra el formulario, invalida cache, muestra toast de éxito.

#### Scenario: editar dirección existente
- **Given** usuario en `/direcciones`, card con alias "Casa"
- **When** presiona "Editar" en esa card
- **Then** se abre `AddressForm` con el campo alias pre-llenado con "Casa"
- **When** modifica linea1 y presiona "Guardar"
- **Then** se hace PUT a `/api/v1/direcciones/{id}`
- **And** aparece toast de éxito "Dirección actualizada"

---

#### REQ-AM-UI-05: Eliminar dirección con confirmación

El botón "Eliminar" en cada `AddressCard` DEBE solicitar confirmación antes de hacer DELETE. En éxito: invalida cache y muestra toast de éxito.

#### Scenario: eliminar dirección confirmando
- **Given** usuario en `/direcciones` con al menos una dirección
- **When** presiona "Eliminar" y confirma la acción
- **Then** se hace DELETE a `/api/v1/direcciones/{id}`
- **And** la dirección desaparece del listado
- **And** aparece toast de éxito "Dirección eliminada"

#### Scenario: cancelar eliminación
- **Given** usuario presiona "Eliminar"
- **When** cancela la confirmación
- **Then** NO se hace ninguna request al backend

---

#### REQ-AM-UI-06: Marcar como predeterminada

El botón "Marcar predeterminada" DEBE aparecer solo en las direcciones que NO son predeterminadas. Al presionar hace PATCH al backend. En éxito: invalida cache, actualiza los badges en el listado.

#### Scenario: marcar una dirección como predeterminada
- **Given** usuario con 2 direcciones, la primera es predeterminada
- **When** presiona "Marcar predeterminada" en la segunda
- **Then** se hace PATCH a `/api/v1/direcciones/{id}/predeterminada`
- **And** la segunda dirección pasa a mostrar Badge "Predeterminada"
- **And** la primera deja de mostrar el badge

#### Scenario: botón oculto en dirección predeterminada
- **Given** una dirección con `es_predeterminada=true`
- **Then** el botón "Marcar predeterminada" NO es visible en esa card

---

#### REQ-AM-UI-07: Estructura FSD

El feature DEBE seguir la estructura FSD estricta. Imports usan siempre path alias `@/`.

```
frontend/src/features/addresses/
├── components/
│   ├── AddressCard.tsx
│   └── AddressForm.tsx
├── hooks/
│   ├── useAddresses.ts
│   ├── useCreateAddress.ts
│   ├── useUpdateAddress.ts
│   ├── useSetPredeterminada.ts
│   └── useDeleteAddress.ts
├── types/
│   └── index.ts
└── __tests__/
    ├── AddressCard.test.tsx
    ├── AddressForm.test.tsx
    └── useAddresses.test.ts

frontend/src/pages/
└── MyAddressesPage.tsx
```

#### Scenario: import correcto
- **Given** cualquier archivo en `features/addresses/`
- **Then** los imports usan `@/shared/...`, `@/features/addresses/...`, nunca rutas relativas que salten capas FSD

---

#### REQ-AM-UI-08: Feedback de errores HTTP

Los errores HTTP del backend (400, 404, 500) DEBEN mostrarse como toasts de error vía el interceptor Axios existente en `@/shared/api/axios.ts`. No se requiere handling adicional en los hooks — el interceptor ya dispara los toasts.

#### Scenario: error 400 al crear dirección
- **Given** el backend responde 400 a POST /direcciones
- **Then** el interceptor Axios muestra un toast de error con el mensaje del backend
- **And** el formulario permanece abierto
