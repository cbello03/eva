import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { exercisesApi } from './api';

export const useStartLesson = (lessonId: string) => {
  return useQuery({
    queryKey: ['lessonSession', lessonId],
    queryFn: () => exercisesApi.startLesson(lessonId),
    refetchOnWindowFocus: false, // Evita reiniciar la lección al cambiar de pestaña
  });
};

export const useSubmitAnswer = (lessonId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ exerciseId, answer }: { exerciseId: number; answer: any }) => 
      exercisesApi.submitAnswer(exerciseId, answer),
    onSuccess: () => {
      // Recargar la sesión de la lección para obtener el siguiente ejercicio o el estado final
      queryClient.invalidateQueries({ queryKey: ['lessonSession', lessonId] });
    },
  });
};