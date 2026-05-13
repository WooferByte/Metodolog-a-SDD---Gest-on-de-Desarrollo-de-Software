/**
 * TypeScript contracts for the profile feature.
 * Mirrors backend schemas: usuarios/perfil_schemas.py + usuarios/schemas.py (UsuarioResponse)
 */

/**
 * Profile data returned by GET /api/v1/perfil and PUT /api/v1/perfil.
 * Matches UsuarioResponse from the backend.
 */
export interface PerfilData {
  id: number
  email: string
  nombre: string
  telefono: string | null
  roles: string[]
  creado_en: string // ISO 8601
}

/**
 * Payload for PUT /api/v1/perfil.
 * At least one field must be provided (validated on the backend with 422 otherwise).
 */
export interface UpdatePerfilPayload {
  nombre?: string
  telefono?: string
}

/**
 * Payload for POST /api/v1/perfil/cambiar-password.
 * Returns 204 No Content on success.
 */
export interface ChangePasswordPayload {
  password_actual: string
  nueva_password: string
}
