import { apiClient } from '../../lib/api-client';
import { Course } from '../courses/types';

export interface CourseAnalytics {
  course_id: number;
  course_title: string;
  total_students: number;
  average_completion: number; // Porcentaje promedio de completación
  average_score: number; // Puntaje promedio en ejercicios
}

export const teacherApi = {
  getMyCourses: async () => {
    const response = await apiClient.get<Course[]>('/teacher/courses');
    return response.data;
  },
  getAnalytics: async () => {
    const response = await apiClient.get<CourseAnalytics[]>('/teacher/analytics');
    return response.data;
  },
  // Aquí irían más endpoints como createUnit, createLesson, etc.
};