import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import { useAuthStore } from "@/features/auth/store";

// Extend Axios config to track retry state
interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// Flag to prevent concurrent refresh attempts
let isRefreshing = false;
// Queue of requests waiting for token refresh
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null): void {
  for (const pending of failedQueue) {
    if (error) {
      pending.reject(error);
    } else {
      pending.resolve(token!);
    }
  }
  failedQueue = [];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Axios instance configured for the EVA backend API.
 * - baseURL: points directly to the Django backend
 * - withCredentials: true (sends httpOnly cookies for refresh token)
 * - Request interceptor: attaches Bearer token from Zustand store
 * - Response interceptor: handles 401 (token refresh), 403, 429, 5xx
 */
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor ──────────────────────────────────────────────
// Attach the in-memory Access_Token as a Bearer header on every request.
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

// ── Response Interceptor ─────────────────────────────────────────────
// Handles:
//   401 → attempt token refresh once, then retry; second 401 → redirect to login
//   403 → access denied
//   429 → rate limited (Retry-After)
//   5xx → generic server error
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;

    if (!originalRequest || !error.response) {
      return Promise.reject(error);
    }

    const status = error.response.status;

    // ── 401 Unauthorized: attempt token refresh ──
    if (status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Another refresh is in progress — queue this request
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Call refresh endpoint — the Refresh_Token is sent automatically
        // via the httpOnly cookie (withCredentials: true).
        const { data } = await axios.post<{ access_token: string }>(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          {},
          { withCredentials: true },
        );

        const newToken = data.access_token;
        useAuthStore.getState().setAccessToken(newToken);

        // Resolve all queued requests with the new token
        processQueue(null, newToken);

        // Retry the original request with the fresh token
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed — clear auth state and redirect to login
        processQueue(refreshError, null);
        useAuthStore.getState().logout();

        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // ── Second 401 (after retry already attempted) → redirect to login ──
    if (status === 401 && originalRequest._retry) {
      useAuthStore.getState().logout();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }

    // ── 403 Forbidden: access denied ──
    if (status === 403) {
      const message =
        (error.response.data as { detail?: string })?.detail ??
        "You do not have permission to perform this action.";
      console.error("[API] Access denied:", message);
      // Surface a structured error for UI consumption
      return Promise.reject(
        new ApiError(403, "ACCESS_DENIED", message),
      );
    }

    // ── 429 Too Many Requests: rate limited ──
    if (status === 429) {
      const retryAfter = error.response.headers["retry-after"];
      const seconds = retryAfter ? Number(retryAfter) : undefined;
      const message = seconds
        ? `Too many requests. Please try again in ${seconds} seconds.`
        : "Too many requests. Please try again later.";
      console.warn("[API] Rate limited:", message);
      return Promise.reject(
        new ApiError(429, "RATE_LIMITED", message, seconds),
      );
    }

    // ── 5xx Server Error: generic error ──
    if (status >= 500) {
      console.error("[API] Server error:", status, error.response.data);
      return Promise.reject(
        new ApiError(
          status,
          "SERVER_ERROR",
          "An unexpected server error occurred. Please try again later.",
        ),
      );
    }

    return Promise.reject(error);
  },
);

// ── Custom error class for structured API errors ─────────────────────
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    /** Retry-After value in seconds (only for 429 responses) */
    public retryAfter?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export default apiClient;
