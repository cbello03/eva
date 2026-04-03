import { useQuery } from '@tanstack/react-query';
import { teacherApi } from './api';
import { useAuthStore } from '../auth/store';

export const useTeacherCourses = () => {
  const user = useAuthStore((state) => state.user);
  return useQuery({
    queryKey: ['teacher', 'courses'],
    queryFn: teacherApi.getMyCourses,
    // Solo habilitado si el usuario existe y es profesor o admin
    enabled: !!user && (user.role === 'teacher' || user.role === 'admin'),
  });
};

export const useTeacherAnalytics = () => {
  const user = useAuthStore((state) => state.user);
  return useQuery({
    queryKey: ['teacher', 'analytics'],
    queryFn: teacherApi.getAnalytics,
    enabled: !!user && (user.role === 'teacher' || user.role === 'admin'),
  });
};