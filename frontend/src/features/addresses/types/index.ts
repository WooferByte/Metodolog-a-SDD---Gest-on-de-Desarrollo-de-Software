/**
 * Address feature types.
 *
 * DireccionResponse  — shape returned by the backend for all address operations
 * DireccionCreate    — payload for POST /api/v1/direcciones
 * DireccionUpdate    — payload for PUT /api/v1/direcciones/{id} (all optional)
 * AddressFormData    — internal React form state (all strings for controlled inputs)
 */

export interface DireccionResponse {
  id: number
  usuario_id: number
  alias: string
  linea1: string
  piso: string | null
  departamento: string | null
  ciudad: string
  codigo_postal: string
  referencia: string | null
  es_predeterminada: boolean
  creado_en: string
  actualizado_en: string
}

export interface DireccionCreate {
  alias: string
  linea1: string
  ciudad: string
  codigo_postal: string
  piso?: string
  departamento?: string
  referencia?: string
  es_predeterminada?: boolean
}

export interface DireccionUpdate {
  alias?: string
  linea1?: string
  ciudad?: string
  codigo_postal?: string
  piso?: string
  departamento?: string
  referencia?: string
  es_predeterminada?: boolean
}

/** Internal React form state — all strings to drive controlled inputs */
export interface AddressFormData {
  alias: string
  linea1: string
  ciudad: string
  codigo_postal: string
  piso: string
  departamento: string
  referencia: string
}
