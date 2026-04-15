import { describe, it, expect, beforeEach, vi } from "vitest";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/features/auth/store";

// Mock the standalone axios default export used for the refresh call inside the interceptor
vi.mock("axios", async (importOriginal) => {
  const actual = await importOriginal<typeof import("axios")>();
  return {
    ...actual,
    default: {
      ...actual.default,
      create: actual.default.create,
      post: vi.fn(),
    },
  };
});

// Must import AFTER the mock is set up
const { apiClient, ApiError } = await import("@/lib/api-client");
const axiosModule = await import("axios");
const axios = axiosModule.default;
const { AxiosHeaders } = axiosModule;

type InterceptorHandler<TIn, TOut = TIn> = {
  fulfilled?: (value: TIn) => TOut | Promise<TOut>;
  rejected?: (error: unknown) => unknown;
};

type InterceptorWithHandlers<TIn, TOut = TIn> = {
  handlers: InterceptorHandler<TIn, TOut>[];
};

// Helper to get interceptor handlers
function getRequestInterceptor() {
  const manager = apiClient.interceptors.request as unknown as InterceptorWithHandlers<InternalAxiosRequestConfig>;
  return manager.handlers[0]?.fulfilled;
}

function getResponseRejected() {
  const manager = apiClient.interceptors.response as unknown as InterceptorWithHandlers<unknown, unknown>;
  return manager.handlers[0]?.rejected;
}

describe("apiClient", () => {
  beforeEach(() => {
    useAuthStore.setState({
      accessToken: null,
      user: null,
      isAuthenticated: false,
    });
    vi.clearAllMocks();
  });

  describe("request interceptor", () => {
    it("attaches Bearer token when accessToken is set", () => {
      useAuthStore.getState().setAccessToken("my-jwt-token");

      const config = {
        headers: new AxiosHeaders(),
      } as InternalAxiosRequestConfig;

      const result = getRequestInterceptor()(config);
      expect(result.headers.Authorization).toBe("Bearer my-jwt-token");
    });

    it("does not attach Authorization header when no token is set", () => {
      const config = {
        headers: new AxiosHeaders(),
      } as InternalAxiosRequestConfig;

      const result = getRequestInterceptor()(config);
      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe("response interceptor — 401 token refresh", () => {
    it("calls refresh endpoint on 401 and updates the store", async () => {
      useAuthStore.getState().setAccessToken("expired-token");

      (axios.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        data: { access_token: "fresh-token" },
      });

      const originalConfig = {
        headers: new AxiosHeaders(),
        _retry: false,
      } as InternalAxiosRequestConfig & { _retry?: boolean };

      const error = {
        config: originalConfig,
        response: { status: 401 },
      } as AxiosError;

      // The interceptor will call refresh, update store, then retry via apiClient().
      // The retry will fail (no server), but we verify the refresh call and store update.
      try {
        await getResponseRejected()(error);
      } catch {
        // Expected — retry request fails without a real server
      }

      expect(axios.post).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/auth/refresh",
        {},
        { withCredentials: true },
      );
      expect(useAuthStore.getState().accessToken).toBe("fresh-token");
    });

    it("logs out when refresh fails", async () => {
      useAuthStore.getState().setAccessToken("expired-token");

      (axios.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("refresh failed"),
      );

      const originalConfig = {
        headers: new AxiosHeaders(),
        _retry: false,
      } as InternalAxiosRequestConfig & { _retry?: boolean };

      const error = {
        config: originalConfig,
        response: { status: 401 },
      } as AxiosError;

      await expect(getResponseRejected()(error)).rejects.toThrow("refresh failed");

      const state = useAuthStore.getState();
      expect(state.accessToken).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("response interceptor — error mapping", () => {
    it("maps 403 to ApiError with ACCESS_DENIED code", async () => {
      const error = {
        config: { headers: new AxiosHeaders() },
        response: {
          status: 403,
          data: { detail: "Not allowed" },
          headers: {},
        },
      } as unknown as AxiosError;

      try {
        await getResponseRejected()(error);
        expect.unreachable("should have thrown");
      } catch (e: unknown) {
        expect(e).toBeInstanceOf(ApiError);
        const apiError = e as ApiError;
        expect(apiError.status).toBe(403);
        expect(apiError.code).toBe("ACCESS_DENIED");
        expect(apiError.message).toBe("Not allowed");
      }
    });

    it("maps 429 to ApiError with RATE_LIMITED code and retryAfter", async () => {
      const error = {
        config: { headers: new AxiosHeaders() },
        response: {
          status: 429,
          data: {},
          headers: { "retry-after": "30" },
        },
      } as unknown as AxiosError;

      try {
        await getResponseRejected()(error);
        expect.unreachable("should have thrown");
      } catch (e: unknown) {
        expect(e).toBeInstanceOf(ApiError);
        const apiError = e as ApiError;
        expect(apiError.status).toBe(429);
        expect(apiError.code).toBe("RATE_LIMITED");
        expect(apiError.retryAfter).toBe(30);
      }
    });

    it("maps 5xx to ApiError with SERVER_ERROR code", async () => {
      const error = {
        config: { headers: new AxiosHeaders() },
        response: {
          status: 500,
          data: { error: "internal" },
          headers: {},
        },
      } as unknown as AxiosError;

      try {
        await getResponseRejected()(error);
        expect.unreachable("should have thrown");
      } catch (e: unknown) {
        expect(e).toBeInstanceOf(ApiError);
        const apiError = e as ApiError;
        expect(apiError.status).toBe(500);
        expect(apiError.code).toBe("SERVER_ERROR");
      }
    });

    it("rejects with original error for unhandled status codes", async () => {
      const error = {
        config: { headers: new AxiosHeaders() },
        response: {
          status: 422,
          data: { detail: "Validation error" },
          headers: {},
        },
      } as unknown as AxiosError;

      await expect(getResponseRejected()(error)).rejects.toBe(error);
    });
  });
});
