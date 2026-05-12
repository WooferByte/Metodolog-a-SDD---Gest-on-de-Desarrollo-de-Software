/**
 * Axios error-mapping interceptor tests
 *
 * Covers the new behavior added in frontend-error-handling-global:
 * - getErrorMessage helper maps status codes to messages + toast types
 * - Response interceptor dispatches addToast for non-401 HTTP errors
 * - Network errors (no response) dispatch "Sin conexión" toast
 * - 401 flow remains unmodified (no toast dispatched)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { AxiosError, AxiosHeaders, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../store/authStore'
import { useUIStore } from '../../../store/uiStore'
import { getErrorMessage, apiClient } from '../axios'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a minimal AxiosError with an HTTP response */
function makeAxiosError(status: number, detail?: string): AxiosError {
  const headers = new AxiosHeaders()
  const requestConfig: InternalAxiosRequestConfig = {
    headers,
    url: '/api/v1/test',
    method: 'get',
  }
  const err = new AxiosError(
    `Request failed with status ${status}`,
    String(status),
    requestConfig,
    undefined,
    {
      status,
      data: detail ? { detail } : {},
      headers,
      config: requestConfig,
      statusText: String(status),
    },
  )
  return err
}

/** Build a network-level AxiosError (no response) */
function makeNetworkError(): AxiosError {
  const headers = new AxiosHeaders()
  const requestConfig: InternalAxiosRequestConfig = {
    headers,
    url: '/api/v1/test',
    method: 'get',
  }
  const err = new AxiosError(
    'Network Error',
    'ERR_NETWORK',
    requestConfig,
    undefined,
    // No response — simulates a pure network failure
    undefined,
  )
  return err
}

/** Extract the response error handler from the apiClient interceptor stack */
function getResponseErrorHandler() {
  const handlers = (apiClient.interceptors.response as unknown as {
    handlers: Array<{
      fulfilled: (r: unknown) => unknown
      rejected: (e: unknown) => unknown
    } | null>
  }).handlers

  const handler = handlers.find((h) => h !== null)
  if (!handler) throw new Error('No response handler found')
  return handler.rejected
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  useAuthStore.setState({
    accessToken: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
    _hasHydrated: false,
  })
  useUIStore.setState({ toasts: [] })
  localStorage.clear()

  Object.defineProperty(window, 'location', {
    writable: true,
    value: { href: '' },
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

// ---------------------------------------------------------------------------
// Unit tests for getErrorMessage helper
// ---------------------------------------------------------------------------

describe('getErrorMessage helper', () => {
  it('maps status 400 → warning', () => {
    const { type } = getErrorMessage(400)
    expect(type).toBe('warning')
  })

  it('maps status 400 with fallback message', () => {
    const { message } = getErrorMessage(400)
    expect(message).toBe('Datos inválidos. Revisá los campos.')
  })

  it('maps status 403 → error', () => {
    const { type } = getErrorMessage(403)
    expect(type).toBe('error')
  })

  it('maps status 404 → info', () => {
    const { type } = getErrorMessage(404)
    expect(type).toBe('info')
  })

  it('maps status 422 → warning', () => {
    const { type } = getErrorMessage(422)
    expect(type).toBe('warning')
  })

  it('maps status 429 → warning', () => {
    const { type } = getErrorMessage(429)
    expect(type).toBe('warning')
  })

  it('maps status 500 → error', () => {
    const { type } = getErrorMessage(500)
    expect(type).toBe('error')
  })

  it('maps unknown status → error with fallback message', () => {
    const { type, message } = getErrorMessage(502)
    expect(type).toBe('error')
    expect(message).toBe('Ocurrió un error inesperado.')
  })

  it('uses RFC 7807 detail when provided', () => {
    const { message } = getErrorMessage(400, 'El campo email ya existe.')
    expect(message).toBe('El campo email ya existe.')
  })

  it('still uses correct type even when detail overrides message', () => {
    const { type } = getErrorMessage(403, 'Acción prohibida.')
    expect(type).toBe('error')
  })
})

// ---------------------------------------------------------------------------
// Integration: interceptor dispatches toasts for non-401 errors
// ---------------------------------------------------------------------------

describe('Response interceptor — error toast dispatch', () => {
  it('dispatches addToast with type "warning" for status 400', async () => {
    const errorHandler = getResponseErrorHandler()
    const error400 = makeAxiosError(400)

    await expect(errorHandler(error400)).rejects.toBeDefined()

    const toasts = useUIStore.getState().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].type).toBe('warning')
    expect(toasts[0].message).toBe('Datos inválidos. Revisá los campos.')
  })

  it('dispatches addToast with type "error" for status 403', async () => {
    const errorHandler = getResponseErrorHandler()
    const error403 = makeAxiosError(403)

    await expect(errorHandler(error403)).rejects.toBeDefined()

    const toasts = useUIStore.getState().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].type).toBe('error')
  })

  it('dispatches addToast with type "error" for status 500', async () => {
    const errorHandler = getResponseErrorHandler()
    const error500 = makeAxiosError(500)

    await expect(errorHandler(error500)).rejects.toBeDefined()

    const toasts = useUIStore.getState().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].type).toBe('error')
    expect(toasts[0].message).toBe('Error del servidor. Intentá más tarde.')
  })

  it('uses RFC 7807 detail from response body when present', async () => {
    const errorHandler = getResponseErrorHandler()
    const error422 = makeAxiosError(422, 'El campo precio debe ser mayor a 0.')

    await expect(errorHandler(error422)).rejects.toBeDefined()

    const toasts = useUIStore.getState().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].message).toBe('El campo precio debe ser mayor a 0.')
    expect(toasts[0].type).toBe('warning')
  })

  it('dispatches "Sin conexión" toast for network errors (no response)', async () => {
    const errorHandler = getResponseErrorHandler()
    const networkErr = makeNetworkError()

    await expect(errorHandler(networkErr)).rejects.toBeDefined()

    const toasts = useUIStore.getState().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].type).toBe('error')
    expect(toasts[0].message).toBe('Sin conexión. Verificá tu red.')
  })

  it('does NOT dispatch toast for 401 (handled by refresh flow)', async () => {
    // We need to short-circuit the 401 path by marking the request as _retry
    // so it returns immediately without attempting refresh.
    const handlers = (apiClient.interceptors.response as unknown as {
      handlers: Array<{
        fulfilled: (r: unknown) => unknown
        rejected: (e: unknown) => unknown
      } | null>
    }).handlers

    const handler = handlers.find((h) => h !== null)!

    const headers = new AxiosHeaders()
    const requestConfig = {
      headers,
      url: '/api/v1/test',
      method: 'get',
      _retry: true, // prevents infinite loop
    } as InternalAxiosRequestConfig & { _retry?: boolean }

    const err401 = new AxiosError(
      'Unauthorized',
      '401',
      requestConfig,
      undefined,
      {
        status: 401,
        data: {},
        headers,
        config: requestConfig,
        statusText: '401',
      },
    )

    await expect(handler.rejected(err401)).rejects.toBeDefined()

    // No toast should have been dispatched for 401
    const toasts = useUIStore.getState().toasts
    expect(toasts).toHaveLength(0)
  })
})
