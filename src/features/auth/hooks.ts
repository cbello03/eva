import { useMutation, useQuery } from '@tanstack/react-query';
import { authApi, LoginData, RegisterData } from './api';
import { useAuthStore } from './store';
// import { useNavigate } from '@tanstack/react-router'; // Lo usaremos más adelante

export const useLogin = () => {
  const setAccessToken = useAuthStore((state) => state.setAccessToken);
  // const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: LoginData) => authApi.login(data),
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      // Opcional: invalidar queries o forzar la carga del usuario aquí
      // navigate({ to: '/dashboard' });
    },
  });
};

export const useRegister = () => {
  // const navigate = useNavigate();
  return useMutation({
    mutationFn: (data: RegisterData) => authApi.register(data),
    onSuccess: () => {
      // Generalmente después de registrar, enviamos al login
      // navigate({ to: '/login' });
    },
  });
};

export const useLogout = () => {
  const logoutStore = useAuthStore((state) => state.logout);
  // const navigate = useNavigate();

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      logoutStore();
      // navigate({ to: '/login' });
    },
  });
};

export const useUser = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const setUser = useAuthStore((state) => state.setUser);

  return useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const user = await authApi.getMe();
      setUser(user);
      return user;
    },
    enabled: isAuthenticated, // Solo busca el usuario si tenemos un token en memoria
  });
};