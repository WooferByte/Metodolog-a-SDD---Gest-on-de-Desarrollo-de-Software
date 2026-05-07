import axios, { AxiosInstance } from 'axios'

/**
 * Factory function to create a configured Axios instance
 * @param baseURL - The base URL for API requests
 * @returns Configured Axios instance
 */
export function createAxiosClient(baseURL: string): AxiosInstance {
  const client = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  /**
   * Response interceptor placeholder
   * Auth interceptor will be added in CHANGE 7
   */
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      // Error handling will be enhanced in future changes
      console.error('API Error:', error)
      return Promise.reject(error)
    }
  )

  return client
}

/**
 * Singleton Axios instance for app-wide use
 * Reads VITE_API_BASE_URL from environment variables
 */
export const apiClient = createAxiosClient(
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
)

/**
 * Alias for apiClient for convenience
 */
export const axiosInstance = apiClient
