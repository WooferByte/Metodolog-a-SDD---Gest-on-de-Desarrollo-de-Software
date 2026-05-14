import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../store/authStore'
import { useUIStore } from '../../store/uiStore'
import type { UIStore } from '../../store/types'
import type { ApiError } from '../types/api'

// ---------------------------------------------------------------------------
// Pending-queue helpers (Tasks 2.1 – 2.3)
// Serialise concurrent 401 responses behind a single refresh call
// ---------------------------------------------------------------------------

let isRefreshing = false
let pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (error: unknown) => void
}> = []

/** Resolve every queued request with the new access token and clear the queue */
function drainQueue(token: string): void {
  pendingQueue.forEach(({ resolve }) => resolve(token))
  pendingQueue = []
}

/** Reject every queued request with the given error and clear the queue */
function rejectQueue(error: unknown): void {
  pendingQueue.forEach(({ reject }) => reject(error))
  pendingQueue = []
}

// ---------------------------------------------------------------------------
// Plain axios instance for refresh calls (Task 3.1)
// No interceptors attached — prevents the refresh call from re-entering the
// JWT response interceptor and causing an infinite loop
// ---------------------------------------------------------------------------
const refreshAxios = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

// ---------------------------------------------------------------------------
// Factory function (Task 4.3)
// Creates a plain configured Axios instance.
// Auth interceptors are NOT wired here — wiring happens once at module level
// on the singleton `apiClient`. This keeps the factory safe to use in tests.
// ---------------------------------------------------------------------------

/**
 * Factory function to create a configured Axios instance
 * @param baseURL - The base URL for API requests
 * @returns Configured Axios instance
 */
export function createAxiosClient(baseURL: string): AxiosInstance {
  return axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
    },
  })
}

// ---------------------------------------------------------------------------
// Singleton instance (Tasks 4.1 – 4.2)
// ---------------------------------------------------------------------------

/**
 * Singleton Axios instance for app-wide use.
 * Reads VITE_API_BASE_URL from environment variables.
 * JWT request + response interceptors are wired below.
 */
export const apiClient = createAxiosClient(
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
)

/**
 * Alias for apiClient for convenience
 */
export const axiosInstance = apiClient

// ---------------------------------------------------------------------------
// Request interceptor (Tasks 1.2 – 1.4)
// Attaches Authorization header from authStore.getState() at request time,
// NOT at instance-creation time, so token refreshes are reflected immediately.
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = useAuthStore.getState().accessToken
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error: unknown) => Promise.reject(error),
)

// ---------------------------------------------------------------------------
// safeString — normalise unknown values to string | undefined (BUG 1 fix)
// Prevents React crash when RFC 7807 `detail` is an object, array, or null
// instead of a plain string. This is the single normalisation point; any
// value that reaches addToast via this path will always be a string.
// ---------------------------------------------------------------------------

/**
 * Converts any unknown value to a safe string or undefined.
 *
 * - string  → returned as-is
 * - object with `detail` property → recurse into detail
 * - other object / array → JSON.stringify
 * - null / undefined → undefined
 */
export function safeString(value: unknown): string | undefined {
  if (value === undefined || value === null) return undefined
  if (typeof value === 'string') return value
  if (
    typeof value === 'object' &&
    'detail' in (value as object)
  ) {
    return safeString((value as Record<string, unknown>).detail)
  }
  return JSON.stringify(value)
}

// ---------------------------------------------------------------------------
// Error message mapping — RFC 7807 status codes to user-friendly messages
// Design decision D-4: prioritise `detail` from RFC 7807 response body;
// fall back to fixed Spanish messages per status code.
// ---------------------------------------------------------------------------

type ToastType = UIStore['toasts'][0]['type']

/**
 * Maps an HTTP status code to a user-friendly message and toast severity.
 *
 * If the backend provided a RFC 7807 `detail` field, that message takes
 * precedence over the fallback string — it is more contextual.
 */
export function getErrorMessage(
  status: number,
  detail?: string,
): { message: string; type: ToastType } {
  const messageMap: Record<number, { message: string; type: ToastType }> = {
    400: { message: 'Datos inválidos. Revisá los campos.', type: 'warning' },
    403: { message: 'No tenés permiso para esta acción.', type: 'error' },
    404: { message: 'El recurso solicitado no existe.', type: 'info' },
    422: {
      message: 'Error de validación en los datos enviados.',
      type: 'warning',
    },
    429: {
      message: 'Demasiadas solicitudes. Esperá un momento.',
      type: 'warning',
    },
    500: { message: 'Error del servidor. Intentá más tarde.', type: 'error' },
  }

  const fallback: { message: string; type: ToastType } = {
    message: 'Ocurrió un error inesperado.',
    type: 'error',
  }

  const mapped = messageMap[status] ?? fallback
  return {
    message: detail ?? mapped.message,
    type: mapped.type,
  }
}

// ---------------------------------------------------------------------------
// Response interceptor — refresh flow (Tasks 3.2 – 3.7)
// ---------------------------------------------------------------------------
apiClient.interceptors.response.use(
  // Success path — pass through unchanged
  (response) => response,

  // Error path
  async (error: unknown) => {
    // Network error or non-Axios error (no response object)
    if (!axios.isAxiosError(error) || !error.response) {
      // Dispatch a "no connection" toast for network-level failures
      useUIStore.getState().addToast({
        message: 'Sin conexión. Verificá tu red.',
        type: 'error',
      })
      return Promise.reject(error)
    }

    const status = error.response.status
    const originalConfig = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // Non-401 errors: map to toast and reject
    if (status !== 401) {
      const rfcDetail = safeString((error.response.data as Partial<ApiError>)?.detail)
      const { message, type } = getErrorMessage(status, rfcDetail)
      useUIStore.getState().addToast({ message, type })
      return Promise.reject(error)
    }

    // Prevent retrying the retry itself to avoid infinite loops
    if (originalConfig._retry) {
      return Promise.reject(error)
    }

    // --- Another refresh is already in flight (Task 3.3) ---
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        pendingQueue.push({ resolve, reject })
      }).then((newToken) => {
        originalConfig._retry = true
        originalConfig.headers.Authorization = `Bearer ${newToken}`
        return apiClient(originalConfig)
      })
    }

    // --- We are the first 401 — initiate the refresh (Task 3.4) ---
    isRefreshing = true
    originalConfig._retry = true

    try {
      const refreshToken = useAuthStore.getState().refreshToken

      const { data } = await refreshAxios.post<{
        access_token: string
        refresh_token: string
      }>('/api/v1/auth/refresh', { refresh_token: refreshToken })

      // Task 3.5 — update store, drain queue, retry original request
      useAuthStore.getState().updateTokens(data.access_token, data.refresh_token)
      drainQueue(data.access_token)
      isRefreshing = false

      originalConfig.headers.Authorization = `Bearer ${data.access_token}`
      return apiClient(originalConfig)
    } catch (refreshError: unknown) {
      // Task 3.6 — reject queue, logout, redirect
      rejectQueue(refreshError)
      isRefreshing = false
      useAuthStore.getState().logout()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    }
  },
)
