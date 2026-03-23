import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { coursesApi } from './api';

export const useCourses = () => {
  return useQuery({
    queryKey: ['courses'],
    queryFn: coursesApi.listCourses,
  });
};

export const useCourse = (id: string) => {
  return useQuery({
    queryKey: ['courses', id],
    queryFn: () => coursesApi.getCourse(id),
  });
};

export const useEnroll = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (courseId: string) => coursesApi.enroll(courseId),
    onSuccess: (_, courseId) => {
      // Forzar recarga de los datos del curso para reflejar la inscripción
      queryClient.invalidateQueries({ queryKey: ['courses', courseId] });
    },
  });
};