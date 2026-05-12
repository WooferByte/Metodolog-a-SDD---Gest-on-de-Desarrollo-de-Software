/**
 * API Type Definitions — RFC 7807 Problem Details
 *
 * Models the error format returned by the backend for all HTTP errors.
 * Reference: https://datatracker.ietf.org/doc/html/rfc7807
 */

/**
 * RFC 7807 Problem Details object.
 * Backend returns this shape on every non-2xx response.
 *
 * Example:
 * {
 *   "type": "about:blank",
 *   "title": "Unprocessable Entity",
 *   "status": 422,
 *   "detail": "El campo 'email' no es válido.",
 *   "instance": "/api/v1/auth/register"
 * }
 */
export interface ApiError {
  /** A URI reference that identifies the problem type */
  type: string
  /** A short, human-readable summary of the problem type */
  title: string
  /** The HTTP status code */
  status: number
  /** A human-readable explanation specific to this occurrence */
  detail?: string
  /** A URI reference that identifies the specific occurrence */
  instance?: string
}
