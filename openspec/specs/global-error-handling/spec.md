## ADDED Requirements

### Requirement: Error Boundary global con Tailwind v4
El sistema SHALL proveer un componente `ErrorBoundary` (class component React) que envuelva el árbol de la aplicación, capturando errores de renderizado y mostrando una pantalla de fallback estilada con Tailwind v4.

#### Scenario: Renderizado normal sin error
- **WHEN** ningún componente hijo lanza un error durante el renderizado
- **THEN** `ErrorBoundary` renderiza sus hijos sin modificación

#### Scenario: Error de renderizado capturado
- **WHEN** un componente hijo lanza un error durante el renderizado
- **THEN** `ErrorBoundary` muestra la pantalla de fallback con mensaje "¡Algo salió mal!"
- **THEN** la pantalla incluye botón "Recargar Página" que ejecuta `window.location.reload()`
- **THEN** la pantalla incluye link "Ir al inicio" que navega a `/`

#### Scenario: Modo desarrollo muestra stack trace
- **WHEN** el error ocurre y `import.meta.env.MODE === 'development'`
- **THEN** la pantalla de fallback muestra el mensaje del error y el `componentStack`

#### Scenario: Modo producción oculta detalles técnicos
- **WHEN** el error ocurre y `import.meta.env.MODE !== 'development'`
- **THEN** la pantalla de fallback muestra solo el mensaje genérico sin detalles técnicos

### Requirement: Componente ToastContainer
El sistema SHALL proveer un componente `ToastContainer` que renderice las notificaciones del slice `uiStore.toasts` en posición fija en la pantalla.

#### Scenario: Sin toasts activos
- **WHEN** `uiStore.toasts` está vacío
- **THEN** `ToastContainer` no renderiza ningún elemento visible

#### Scenario: Toast aparece al agregar
- **WHEN** `addToast` es llamado con `{ message, type }`
- **THEN** `ToastContainer` renderiza el mensaje con el color correspondiente al tipo (`success` → verde, `error` → rojo, `warning` → amarillo, `info` → azul)
- **THEN** se muestra un ícono de lucide-react apropiado al tipo

#### Scenario: Auto-dismiss por tipo
- **WHEN** un toast es agregado sin `duration` explícita
- **THEN** `success` e `info` se descartan automáticamente a los 4000ms
- **THEN** `warning` se descarta automáticamente a los 5000ms
- **THEN** `error` se descarta automáticamente a los 6000ms

#### Scenario: Auto-dismiss con duración explícita
- **WHEN** un toast es agregado con `duration: N`
- **THEN** el toast se descarta automáticamente a los `N` ms

#### Scenario: Cierre manual de toast
- **WHEN** el usuario hace clic en el botón X de un toast
- **THEN** el toast es eliminado inmediatamente de `uiStore.toasts`

#### Scenario: Límite de toasts simultáneos
- **WHEN** se intenta agregar un toast y ya hay 5 toasts activos
- **THEN** el toast más antiguo es eliminado antes de agregar el nuevo

### Requirement: Tipo ApiError para RFC 7807
El sistema SHALL declarar el tipo TypeScript `ApiError` que modela la respuesta de error RFC 7807 del backend.

#### Scenario: Tipado correcto de respuesta de error
- **WHEN** el interceptor Axios procesa una respuesta con status ≥ 400
- **THEN** `error.response.data` PUEDE ser casteado a `ApiError` con campos `type`, `title`, `status`, `detail`, `instance`

---

## MODIFIED Requirements

### Requirement: Interceptor Axios maneja errores no-401
El interceptor de respuesta de `apiClient` SHALL mapear status codes HTTP a mensajes legibles en español y despacharlos como toasts vía `useUIStore.getState().addToast()`.

#### Scenario: Error 400 Bad Request
- **WHEN** una respuesta HTTP tiene status 400
- **THEN** el interceptor llama `addToast({ message: detail_o_fallback, type: 'warning' })`
- **THEN** el mensaje es `error.response.data.detail` si existe, o "Datos inválidos. Revisá los campos." como fallback

#### Scenario: Error 403 Forbidden
- **WHEN** una respuesta HTTP tiene status 403
- **THEN** el interceptor llama `addToast({ message: detail_o_fallback, type: 'error' })`
- **THEN** el mensaje fallback es "No tenés permiso para esta acción."

#### Scenario: Error 404 Not Found
- **WHEN** una respuesta HTTP tiene status 404
- **THEN** el interceptor llama `addToast({ message: detail_o_fallback, type: 'info' })`
- **THEN** el mensaje fallback es "El recurso solicitado no existe."

#### Scenario: Error 422 Unprocessable Entity
- **WHEN** una respuesta HTTP tiene status 422
- **THEN** el interceptor llama `addToast({ message: detail_o_fallback, type: 'warning' })`
- **THEN** el mensaje fallback es "Error de validación en los datos enviados."

#### Scenario: Error 429 Too Many Requests
- **WHEN** una respuesta HTTP tiene status 429
- **THEN** el interceptor llama `addToast({ message: detail_o_fallback, type: 'warning' })`
- **THEN** el mensaje fallback es "Demasiadas solicitudes. Esperá un momento."

#### Scenario: Error 500 Internal Server Error
- **WHEN** una respuesta HTTP tiene status 500 o superior
- **THEN** el interceptor llama `addToast({ message: detail_o_fallback, type: 'error' })`
- **THEN** el mensaje fallback es "Error del servidor. Intentá más tarde."

#### Scenario: Error de red sin respuesta
- **WHEN** el error Axios no tiene `error.response` (timeout, red caída)
- **THEN** el interceptor llama `addToast({ message: "Sin conexión. Verificá tu red.", type: 'error' })`

#### Scenario: Error 401 — behavior sin cambios
- **WHEN** una respuesta HTTP tiene status 401
- **THEN** el comportamiento de refresh de tokens existente NO es modificado por este change
