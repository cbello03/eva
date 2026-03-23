import { apiClient } from '../../lib/api-client';

export interface GamificationProfile {
  total_xp: number;
  current_level: number;
  current_streak: number;
  longest_streak: number;
}

export interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  is_unlocked: boolean;
  unlocked_at?: string;
}

export const gamificationApi = {
  getProfile: async () => {
    const response = await apiClient.get<GamificationProfile>('/gamification/profile');
    return response.data;
  },
  getLeaderboard: async (period: 'weekly' | 'alltime' = 'alltime') => {
    const response = await apiClient.get(`/gamification/leaderboard?period=${period}`);
    return response.data;
  },
  getAchievements: async () => {
    const response = await apiClient.get<Achievement[]>('/gamification/achievements');
    return response.data;
  }
};