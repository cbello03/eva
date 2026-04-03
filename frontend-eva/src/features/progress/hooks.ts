import { useQuery } from '@tanstack/react-query';
import { progressApi } from './api';
import { useAuthStore } from '../auth/store';

export const useActivityHeatmap = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return useQuery({
    queryKey: ['progress', 'heatmap'],
    queryFn: progressApi.getHeatmap,
    enabled: isAuthenticated,
  });
};

export const useDomainMastery = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return useQuery({
    queryKey: ['progress', 'domains'],
    queryFn: progressApi.getDomainMastery,
    enabled: isAuthenticated,
  });
};