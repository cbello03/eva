import { apiClient } from '../../lib/api-client';

export interface Project {
  id: number;
  course_id: number;
  title: string;
  description: string;
  due_date: string;
  max_file_size_mb: number;
}

export interface Submission {
  id: number;
  project_id: number;
  file_url: string;
  submitted_at: string;
  status: 'pending' | 'reviewed';
  peer_score?: number;
  peer_feedback?: string;
}

export const projectsApi = {
  getProjects: async () => {
    const response = await apiClient.get<Project[]>('/projects');
    return response.data;
  },
  getProject: async (id: string) => {
    const response = await apiClient.get<Project>(`/projects/${id}`);
    return response.data;
  },
  getSubmission: async (projectId: string) => {
    const response = await apiClient.get<Submission>(`/projects/${projectId}/submission`);
    return response.data;
  },
  // ¡Importante! Envío de archivos (multipart/form-data)
  submitProject: async (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<Submission>(`/projects/${projectId}/submit`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};