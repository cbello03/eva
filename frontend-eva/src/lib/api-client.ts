import axios from 'axios'

/**
 * Pre-configured Axios instance for all EVA API calls.
 *
 * - baseURL points to the versioned API prefix
 * - withCredentials ensures the httpOnly Refresh_Token cookie is sent
 */
const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// ---------------------------------------------------------------------------
// Request interceptor — attach Bearer token from Zustand auth store
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use(
  (config) => {
    // TODO: once the auth store is created (features/auth/store.ts),
    // read the access token and attach it:
    //
    // const token = useAuthStore.getState().accessToken
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => Promise.reject(error),
)

// ---------------------------------------------------------------------------
// Response interceptor — handle 401 and trigger token refresh
// ---------------------------------------------------------------------------
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // TODO: once the auth store + refresh endpoint exist, implement
    // automatic token refresh on 401:
    //
    // if (error.response?.status === 401 && !error.config._retry) {
    //   error.config._retry = true
    //   const { accessToken } = await refreshToken()
    //   useAuthStore.getState().setAccessToken(accessToken)
    //   error.config.headers.Authorization = `Bearer ${accessToken}`
    //   return apiClient(error.config)
    // }
    return Promise.reject(error)
  },
)

export default apiClient
