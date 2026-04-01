import axios from 'axios';
import { useAuthStore } from '../features/auth/store';

export const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // Vital para enviar la cookie httpOnly del Refresh Token
});

// Interceptor de Solicitud: Adjuntar el Access Token en memoria
apiClient.interceptors.request.use((config) => {
  const accessToken = useAuthStore.getState().accessToken;
  if (accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Interceptor de Respuesta: Refresh automático y manejo de errores globales
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si recibimos un 401 y no hemos reintentado ya esta misma petición
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Hacemos el post directo con axios para evitar un bucle infinito con nuestro propio interceptor
        const refreshResponse = await axios.post('/api/v1/auth/refresh', {}, {
          withCredentials: true 
        });

        const { access_token } = refreshResponse.data;

        // Actualizamos Zustand con el nuevo token
        useAuthStore.getState().setAccessToken(access_token);

        // Actualizamos el header y reintentamos la petición original
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
        
      } catch (refreshError) {
        // Si el refresh falla (ej. Refresh Token expiró), cerramos sesión por completo
        useAuthStore.getState().logout();
        window.location.href = '/login'; // Redirección forzada al login
        return Promise.reject(refreshError);
      }
    }

    // Manejo de errores de UI (Requisito de la estrategia del Frontend)
    if (error.response?.status === 403) {
      console.error("Acceso denegado: No tienes permisos para esta acción.");
    } else if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      console.warn(`Límite de tasa excedido. Por favor espere ${retryAfter ? retryAfter + ' segundos' : ''}.`);
    } else if (error.response?.status >= 500) {
      console.error("Algo salió mal en el servidor.");
    } else if (!error.response) {
      console.error("Sin conexión de red.");
    }

    return Promise.reject(error);
  }
);