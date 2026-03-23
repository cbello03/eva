import { apiClient } from '../../lib/api-client';
import { Course, Enrollment } from './types';

export const coursesApi = {
  listCourses: async () => {
    const response = await apiClient.get<Course[]>('/courses');
    return response.data;
  },
  getCourse: async (id: string) => {
    const response = await apiClient.get<Course>(`/courses/${id}`);
    return response.data;
  },
  enroll: async (courseId: string) => {
    const response = await apiClient.post<Enrollment>(`/courses/${courseId}/enroll`);
    return response.data;
  },
};