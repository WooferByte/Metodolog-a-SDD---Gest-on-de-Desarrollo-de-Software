## MODIFIED Requirements

### Requirement: Password change validation is server-authoritative
The `ChangePasswordForm` component SHALL validate only format constraints client-side: `passwordActual` and `nuevaPassword` are required and each must be at least 8 characters. The form SHALL NOT compare `nuevaPassword` against `passwordActual` client-side. The backend is the sole authority on whether the current password is correct; its 400 error response SHALL be surfaced via the Axios interceptor toast. Submitting identical strings for both fields is permitted by the client and delegated to the backend for validation.

#### Scenario: Empty current password field
- **WHEN** the user submits the form with `passwordActual` empty
- **THEN** a client-side validation error SHALL appear: "La contraseña actual es requerida."

#### Scenario: Current password too short
- **WHEN** the user submits the form with `passwordActual` having fewer than 8 characters
- **THEN** a client-side validation error SHALL appear: "La contraseña actual debe tener al menos 8 caracteres."

#### Scenario: Empty new password field
- **WHEN** the user submits the form with `nuevaPassword` empty
- **THEN** a client-side validation error SHALL appear: "La nueva contraseña es requerida."

#### Scenario: New password too short
- **WHEN** the user submits the form with `nuevaPassword` having fewer than 8 characters
- **THEN** a client-side validation error SHALL appear: "La nueva contraseña debe tener al menos 8 caracteres."

#### Scenario: Same password strings submitted (allowed by client)
- **WHEN** the user types the same string in both `passwordActual` and `nuevaPassword` and both meet the minimum length
- **THEN** the form SHALL submit the request to the backend and SHALL NOT show a client-side validation error

#### Scenario: Backend rejects wrong current password
- **WHEN** the backend returns 400 with RFC 7807 detail
- **THEN** the Axios interceptor toast SHALL display the error message as a string and the form SHALL remain visible for correction
