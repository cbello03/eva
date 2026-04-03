import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from './api';

export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getProjects,
  });
};

export const useProject = (id: string) => {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => projectsApi.getProject(id),
  });
};

export const useSubmission = (projectId: string) => {
  return useQuery({
    queryKey: ['projects', projectId, 'submission'],
    queryFn: () => projectsApi.getSubmission(projectId),
    retry: false, // Si da 404 es porque no ha entregado nada aún
  });
};

export const useSubmitProject = (projectId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => projectsApi.submitProject(projectId, file),
    onSuccess: () => {
      // Recargar la entrega para mostrar que fue exitosa
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'submission'] });
    },
  });
};