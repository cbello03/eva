import axios from 'axios';
import { useAuthStore } from '../store/auth-store';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api', // La dirección por defecto de Django
  headers: {
    'Content-Type': 'application/json',
  },
});

// Este código pega el Token automáticamente en cada petición si el usuario está logueado
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;