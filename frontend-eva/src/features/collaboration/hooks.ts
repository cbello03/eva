import { useQuery } from '@tanstack/react-query';
import { collaborationApi } from './api';
import { useAuthStore } from '../auth/store';

export const useWorkspace = (workspaceId: string) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  return useQuery({
    queryKey: ['workspace', workspaceId],
    queryFn: () => collaborationApi.getWorkspace(workspaceId),
    enabled: isAuthenticated && !!workspaceId,
    refetchOnWindowFocus: false, // Vital para no sobreescribir el trabajo en vivo si el usuario cambia de pestaña
  });
};