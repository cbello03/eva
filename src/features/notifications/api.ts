import { apiClient } from '../../lib/api-client';

export interface Notification {
  id: number;
  notification_type: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
}

export const notificationsApi = {
  getNotifications: async () => {
    const response = await apiClient.get<{ items: Notification[] }>('/notifications');
    return response.data.items;
  },
  getUnreadCount: async () => {
    const response = await apiClient.get<{ count: number }>('/notifications/unread-count');
    return response.data.count;
  },
  markRead: async (id: number) => {
    await apiClient.post(`/notifications/${id}/read`);
  },
  markAllRead: async () => {
    await apiClient.post('/notifications/read-all');
  },
};