import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { socialApi, chatApi } from './api';
import { useAuthStore } from '../auth/store';

export const useThreads = (courseId: string) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  return useQuery({
    queryKey: ['forum', 'threads', courseId],
    queryFn: () => socialApi.getThreads(courseId),
    enabled: isAuthenticated && !!courseId,
  });
};

export const useCreateThread = (courseId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ title, body }: { title: string; body: string }) => 
      socialApi.createThread(courseId, title, body),
    onSuccess: () => {
      // Recargamos la lista de hilos automáticamente tras crear uno nuevo
      queryClient.invalidateQueries({ queryKey: ['forum', 'threads', courseId] });
    },
  });
};

export const useChatHistory = (courseId: string) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  return useQuery({
    queryKey: ['chat', 'history', courseId],
    queryFn: () => chatApi.getHistory(courseId),
    enabled: isAuthenticated && !!courseId,
    refetchOnWindowFocus: false, // Evitamos recargar el historial si el usuario cambia de pestaña
  });
};