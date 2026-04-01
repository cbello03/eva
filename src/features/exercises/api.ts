import { apiClient } from '../../lib/api-client';
import { LessonSession, AnswerResult } from './types';

export const exercisesApi = {
  startLesson: async (lessonId: string) => {
    const response = await apiClient.get<LessonSession>(`/lessons/${lessonId}/start`);
    return response.data;
  },
  submitAnswer: async (exerciseId: number, answer: any) => {
    const response = await apiClient.post<AnswerResult>(`/exercises/${exerciseId}/submit`, { answer });
    return response.data;
  },
};