import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "@/features/auth/store";

describe("useAuthStore", () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useAuthStore.setState({
      accessToken: null,
      user: null,
      isAuthenticated: false,
    });
  });

  describe("initial state", () => {
    it("starts with null token, null user, and not authenticated", () => {
      const state = useAuthStore.getState();
      expect(state.accessToken).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("setAccessToken", () => {
    it("sets the token and marks authenticated when given a non-null token", () => {
      useAuthStore.getState().setAccessToken("jwt-token-123");

      const state = useAuthStore.getState();
      expect(state.accessToken).toBe("jwt-token-123");
      expect(state.isAuthenticated).toBe(true);
    });

    it("clears the token and marks unauthenticated when given null", () => {
      // First set a token
      useAuthStore.getState().setAccessToken("jwt-token-123");
      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      // Then clear it
      useAuthStore.getState().setAccessToken(null);

      const state = useAuthStore.getState();
      expect(state.accessToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("setUser", () => {
    it("sets the user object", () => {
      const user = {
        id: 1,
        email: "student@example.com",
        display_name: "Test Student",
        role: "student" as const,
        timezone: "UTC",
      };

      useAuthStore.getState().setUser(user);

      const state = useAuthStore.getState();
      expect(state.user).toEqual(user);
    });

    it("clears the user when given null", () => {
      useAuthStore.getState().setUser({
        id: 1,
        email: "student@example.com",
        display_name: "Test Student",
        role: "student" as const,
        timezone: "UTC",
      });

      useAuthStore.getState().setUser(null);
      expect(useAuthStore.getState().user).toBeNull();
    });

    it("does not affect accessToken or isAuthenticated", () => {
      useAuthStore.getState().setAccessToken("token");
      useAuthStore.getState().setUser({
        id: 1,
        email: "a@b.com",
        display_name: "A",
        role: "teacher" as const,
        timezone: "UTC",
      });

      const state = useAuthStore.getState();
      expect(state.accessToken).toBe("token");
      expect(state.isAuthenticated).toBe(true);
    });
  });

  describe("logout", () => {
    it("clears token, user, and sets isAuthenticated to false", () => {
      // Set up authenticated state
      useAuthStore.getState().setAccessToken("jwt-token");
      useAuthStore.getState().setUser({
        id: 1,
        email: "user@example.com",
        display_name: "User",
        role: "admin" as const,
        timezone: "America/New_York",
      });

      // Logout
      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.accessToken).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it("is idempotent — calling logout on already logged-out state is safe", () => {
      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.accessToken).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });
});
