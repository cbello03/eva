import { create } from 'zustand';

// Definición de tipos basada en los esquemas del backend
export interface User {
  id: number;
  email: string;
  display_name: string;
  role: 'student' | 'teacher' | 'admin';
  timezone: string;
}

interface AuthState {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAccessToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null, // Propiedad 51: Almacenado solo en memoria
  user: null,
  isAuthenticated: false,
  setAccessToken: (token) => set({ accessToken: token, isAuthenticated: !!token }),
  setUser: (user) => set({ user }),
  logout: () => set({ accessToken: null, user: null, isAuthenticated: false }),
}));