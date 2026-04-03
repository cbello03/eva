import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from './api';
import { useAuthStore } from '../auth/store';

export const useUnreadCount = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  return useQuery({
    queryKey: ['notifications', 'unreadCount'],
    queryFn: notificationsApi.getUnreadCount,
    enabled: isAuthenticated,
  });
};

export const useNotifications = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: notificationsApi.getNotifications,
    enabled: isAuthenticated,
  });
};

export const useMarkRead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: () => {
      // Forzar recarga de la lista y el conteo para mantener la UI sincronizada
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
};