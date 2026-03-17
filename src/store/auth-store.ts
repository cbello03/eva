import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Definimos la forma del usuario
interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'student' | 'teacher';
}

// Definimos qué guarda el Store
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      token: null,

      setAuth: (user, token) => 
        set({ 
          isAuthenticated: true, 
          user, 
          token 
        }),

      logout: () => 
        set({ 
          isAuthenticated: false, 
          user: null, 
          token: null 
        }),
    }),
    {
      name: 'auth-storage', // Esto lo guarda en el navegador
    }
  )
);