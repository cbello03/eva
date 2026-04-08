import { apiClient } from "@/lib/api-client";

// ── Types ────────────────────────────────────────────────────────────

export interface GroupMember {
  id: number;
  display_name: string;
  joined_at: string;
}

export interface CollabGroup {
  id: number;
  exercise_id: number;
  members: GroupMember[];
  workspace_state: Record<string, unknown>;
  created_at: string;
}

export interface CollabSubmission {
  id: number;
  group_id: number;
  submitted_answer: Record<string, unknown>;
  submitted_at: string;
}

// ── API functions ────────────────────────────────────────────────────

/** Join a collaborative exercise — server assigns a group. */
export async function joinCollabExercise(
  exerciseId: number,
): Promise<CollabGroup> {
  const response = await apiClient.post<CollabGroup>(
    `/exercises/${exerciseId}/collab/join`,
  );
  return response.data;
}

/** Submit group work for a collaborative exercise. */
export async function submitGroupWork(
  groupId: number,
  data: { submitted_answer: Record<string, unknown> },
): Promise<CollabSubmission> {
  const response = await apiClient.post<CollabSubmission>(
    `/collab/groups/${groupId}/submit`,
    data,
  );
  return response.data;
}

/** Get group info and workspace state. */
export async function getGroupInfo(groupId: number): Promise<CollabGroup> {
  const response = await apiClient.get<CollabGroup>(
    `/collab/groups/${groupId}`,
  );
  return response.data;
}
