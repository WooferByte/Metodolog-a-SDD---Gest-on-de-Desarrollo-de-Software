# Axios Interceptor — Error Handling & Toast Dispatch

## Requirements

### Requirement: Mapeo de status codes a mensajes en español
El interceptor de respuesta de `apiClient` SHALL mapear los siguientes status codes HTTP a mensajes legibles en español y despacharlos vía `useUIStore.getState().addToast()`:

| Status | Mensaje | Tipo toast |
|--------|---------|-----------|
| 400 | Datos inválidos. Revisá los campos. | warning |
| 403 | No tenés permiso para esta acción. | error |
| 404 | El recurso solicitado no existe. | info |
| 422 | Error de validación en los datos enviados. | warning |
| 429 | Demasiadas solicitudes. Esperá un momento. | warning |
| 500 | Error del servidor. Intentá más tarde. | error |
| red | Sin conexión. Verificá tu red. | error |

### Requirement: Prioridad RFC 7807
Si el backend devuelve un campo `detail` en el body (RFC 7807), ese mensaje SHOULD tomar precedencia sobre el mensaje fallback del status code.

### Requirement: Flujo 401 intacto
El interceptor NO SHALL modificar el flujo de refresco de tokens 401. Solo los status ≠ 401 y errores de red son mapeados a toasts.

### Requirement: Errores de red
Cuando `error.response` es undefined (sin conectividad), el interceptor SHALL despachar un toast de tipo `error` con mensaje "Sin conexión. Verificá tu red." antes de rechazar la promesa.
