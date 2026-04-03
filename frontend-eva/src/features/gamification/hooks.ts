import { useQuery } from '@tanstack/react-query';
import { gamificationApi } from './api';
import { useAuthStore } from '../auth/store';

export const useGamificationProfile = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return useQuery({
    queryKey: ['gamification', 'profile'],
    queryFn: gamificationApi.getProfile,
    enabled: isAuthenticated,
  });
};

export const useAchievements = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return useQuery({
    queryKey: ['gamification', 'achievements'],
    queryFn: gamificationApi.getAchievements,
    enabled: isAuthenticated,
  });
};

export const useLeaderboard = (period: 'weekly' | 'alltime' = 'alltime') => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return useQuery({
    queryKey: ['gamification', 'leaderboard', period],
    queryFn: () => gamificationApi.getLeaderboard(period),
    enabled: isAuthenticated,
  });
};