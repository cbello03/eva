import { create } from "zustand";
import type { User } from "@/features/auth/api";

interface AuthState {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAccessToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,
  setAccessToken: (token) =>
    set({ accessToken: token, isAuthenticated: token !== null }),
  setUser: (user) => set({ user }),
  logout: () => set({ accessToken: null, user: null, isAuthenticated: false }),
}));
