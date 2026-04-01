import { apiClient } from '../../lib/api-client';

export interface Thread {
  id: number;
  course_id: number;
  title: string;
  author_name: string;
  created_at: string;
  replies_count: number;
}

export interface Post {
  id: number;
  thread_id: number;
  body: string;
  author_name: string;
  created_at: string;
  is_solution: boolean;
}

export const socialApi = {
  getThreads: async (courseId: string) => {
    const response = await apiClient.get<Thread[]>(`/courses/${courseId}/forums/threads`);
    return response.data;
  },
  createThread: async (courseId: string, title: string, body: string) => {
    const response = await apiClient.post<Thread>(`/courses/${courseId}/forums/threads`, { title, body });
    return response.data;
  }
};

export interface ChatMessage {
  id: string; // Usamos string porque los mensajes en tiempo real suelen usar UUIDs temporales
  author_name: string;
  body: string;
  created_at: string;
  is_current_user?: boolean;
}

export const chatApi = {
  getHistory: async (courseId: string) => {
    const response = await apiClient.get<ChatMessage[]>(`/courses/${courseId}/chat/history`);
    return response.data;
  }
};