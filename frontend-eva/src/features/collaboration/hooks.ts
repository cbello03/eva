import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import * as collabApi from "./api";

// ── Query keys ───────────────────────────────────────────────────────

export const collabKeys = {
  group: (groupId: number) => ["collab", "group", groupId] as const,
};

// ── useCollabGroup: get group info and workspace state ───────────────

export function useCollabGroup(groupId: number) {
  return useQuery({
    queryKey: collabKeys.group(groupId),
    queryFn: () => collabApi.getGroupInfo(groupId),
    enabled: groupId > 0,
    refetchInterval: 10_000, // poll for workspace updates
  });
}

// ── useJoinCollab: join a collaborative exercise ─────────────────────

export function useJoinCollab() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: collabApi.joinCollabExercise,
    onSuccess: (group) => {
      queryClient.setQueryData(collabKeys.group(group.id), group);
    },
  });
}

// ── useSubmitGroupWork: submit group work ────────────────────────────

export function useSubmitGroupWork(groupId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { submitted_answer: Record<string, unknown> }) =>
      collabApi.submitGroupWork(groupId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: collabKeys.group(groupId),
      });
    },
  });
}
