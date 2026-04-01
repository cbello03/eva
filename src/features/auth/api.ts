import { apiClient } from '../../lib/api-client';
import { User } from './store';
import { z } from 'zod';

// Esquemas de validación con Zod (compartidos con los formularios)
export const loginSchema = z.object({
  email: z.string().email("Correo electrónico inválido"),
  password: z.string().min(1, "La contraseña es requerida"),
});

export const registerSchema = z.object({
  email: z.string().email("Correo electrónico inválido"),
  display_name: z.string().min(2, "El nombre debe tener al menos 2 caracteres"),
  password: z.string()
    // Requisito del backend: >= 8 caracteres, mayúscula, minúscula, número
    .min(8, "Mínimo 8 caracteres")
    .regex(/[A-Z]/, "Debe contener al menos una mayúscula")
    .regex(/[a-z]/, "Debe contener al menos una minúscula")
    .regex(/[0-9]/, "Debe contener al menos un número"),
});

export type LoginData = z.infer<typeof loginSchema>;
export type RegisterData = z.infer<typeof registerSchema>;

export const authApi = {
  login: async (data: LoginData) => {
    const response = await apiClient.post<{ access_token: string }>('/auth/login', data);
    return response.data;
  },
  register: async (data: RegisterData) => {
    const response = await apiClient.post<User>('/auth/register', data);
    return response.data;
  },
  logout: async () => {
    await apiClient.post('/auth/logout');
  },
  getMe: async () => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};