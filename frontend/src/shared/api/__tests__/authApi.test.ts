/**
 * Tests for logoutUser() API function (task 7.1)
 *
 * Verifies:
 * - Correct HTTP method (POST)
 * - Correct URL (/api/v1/auth/logout)
 * - Correct request body ({ refresh_token: ... })
 * - 204 responses are handled without throwing
 * - Non-2xx errors propagate to the caller
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient } from '../axios'
import { logoutUser } from '../authApi'

describe('logoutUser()', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('7.1.1 calls POST /api/v1/auth/logout with the correct body', async () => {
    const postSpy = vi
      .spyOn(apiClient, 'post')
      .mockResolvedValue({ status: 204, data: undefined })

    await logoutUser('my-refresh-token-xyz')

    expect(postSpy).toHaveBeenCalledOnce()
    expect(postSpy).toHaveBeenCalledWith('/api/v1/auth/logout', {
      refresh_token: 'my-refresh-token-xyz',
    })
  })

  it('7.1.2 resolves without throwing on 204 No Content', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValue({ status: 204, data: undefined })

    // Should not throw
    await expect(logoutUser('some-token')).resolves.toBeUndefined()
  })

  it('7.1.3 propagates errors from the API client (caller handles them)', async () => {
    const networkError = new Error('Network Error')
    vi.spyOn(apiClient, 'post').mockRejectedValue(networkError)

    await expect(logoutUser('some-token')).rejects.toThrow('Network Error')
  })

  it('7.1.4 does not silently swallow 401 errors', async () => {
    const unauthorizedError = Object.assign(new Error('Request failed with status 401'), {
      response: { status: 401, data: { detail: 'Invalid refresh token' } },
    })
    vi.spyOn(apiClient, 'post').mockRejectedValue(unauthorizedError)

    await expect(logoutUser('bad-token')).rejects.toThrow()
  })
})
