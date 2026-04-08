import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/features/auth/store";
import * as authApi from "@/features/auth/api";

// ── Query keys ───────────────────────────────────────────────────────

const authKeys = {
  me: ["auth", "me"] as const,
};

// ── useAuth: full auth state from Zustand ────────────────────────────

export function useAuth() {
  const { accessToken, user, isAuthenticated } = useAuthStore();
  return { accessToken, user, isAuthenticated };
}

// ── useUser: fetches current user from /auth/me ──────────────────────

export function useUser() {
  const { isAuthenticated } = useAuthStore();

  return useQuery({
    queryKey: authKeys.me,
    queryFn: authApi.getMe,
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ── useLogin: mutation for POST /auth/login ──────────────────────────

export function useLogin() {
  const { setAccessToken, setUser } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: async (data) => {
      setAccessToken(data.access_token);

      // Fetch user profile after successful login
      const user = await authApi.getMe();
      setUser(user);
      queryClient.setQueryData(authKeys.me, user);
    },
  });
}

// ── useRegister: mutation for POST /auth/register ────────────────────

export function useRegister() {
  return useMutation({
    mutationFn: authApi.register,
  });
}

// ── useLogout: mutation for POST /auth/logout ────────────────────────

export function useLogout() {
  const { logout } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      logout();
      queryClient.removeQueries({ queryKey: authKeys.me });
    },
  });
}
