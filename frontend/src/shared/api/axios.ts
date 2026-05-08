import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../store/authStore'

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
// Response interceptor — refresh flow (Tasks 3.2 – 3.7)
// ---------------------------------------------------------------------------
apiClient.interceptors.response.use(
  // Success path — pass through unchanged
  (response) => response,

  // Error path
  async (error: unknown) => {
    // Only AxiosErrors with a response object carry a status code
    if (!axios.isAxiosError(error) || !error.response) {
      return Promise.reject(error)
    }

    const status = error.response.status
    const originalConfig = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // Non-401 errors are passed through immediately (Task 3.7)
    if (status !== 401) {
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
