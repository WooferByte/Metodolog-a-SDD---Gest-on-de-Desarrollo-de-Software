## ADDED Requirements

### Requirement: Toast message must always be a primitive string
The Axios response interceptor and any caller of `addToast` SHALL guarantee that the `message` field is a primitive string before it is stored in `uiStore`. Non-string values (objects, arrays, numbers) MUST be coerced to a human-readable string. The `ToastContainer` component SHALL defensively cast `toast.message` via `String()` as a belt-and-suspenders measure.

#### Scenario: Backend returns RFC 7807 with string detail
- **WHEN** the API responds with a non-2xx status and a body `{ "type": "...", "title": "...", "status": 400, "detail": "Contraseña incorrecta." }`
- **THEN** the toast `message` SHALL be the string `"Contraseña incorrecta."` and React SHALL render it without crashing

#### Scenario: Backend returns RFC 7807 with object detail
- **WHEN** the API responds with a non-2xx status and `detail` is a nested object or array
- **THEN** the interceptor MUST coerce the value to a JSON string before calling `addToast`, and the toast SHALL render without crashing

#### Scenario: Backend returns RFC 7807 without detail
- **WHEN** the API responds with a non-2xx status and `detail` is absent or `null`
- **THEN** the interceptor MUST fall back to the fixed Spanish message from `getErrorMessage` (e.g. "Datos inválidos. Revisá los campos.")

#### Scenario: Non-RFC 7807 network error
- **WHEN** the request fails at the network level (no response object)
- **THEN** the toast MUST show "Sin conexión. Verificá tu red." as a string

#### Scenario: ToastContainer renders unknown message type
- **WHEN** any caller passes a non-string value as `message` to `addToast`
- **THEN** `ToastContainer` SHALL render `String(message)` and not throw a React render error
