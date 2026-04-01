import { apiClient } from '../../lib/api-client';

export interface Workspace {
  id: string;
  name: string;
  project_id: number;
  content: string; // El contenido inicial del documento
}

export const collaborationApi = {
  getWorkspace: async (workspaceId: string) => {
    const response = await apiClient.get<Workspace>(`/collaboration/workspaces/${workspaceId}`);
    return response.data;
  }
};