import { apiClient } from '../../lib/api-client';

export interface DailyActivity {
  date: string;
  activity_count: number;
  level: 0 | 1 | 2 | 3 | 4; // 0 = sin actividad, 4 = mucha actividad (para los colores)
}

export interface DomainMastery {
  id: number;
  domain_name: string;
  mastery_percentage: number;
}

export const progressApi = {
  getHeatmap: async () => {
    const response = await apiClient.get<DailyActivity[]>('/progress/heatmap');
    return response.data;
  },
  getDomainMastery: async () => {
    const response = await apiClient.get<DomainMastery[]>('/progress/domains');
    return response.data;
  }
};