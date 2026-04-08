import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import * as projectsApi from "./api";

// ── Query keys ───────────────────────────────────────────────────────

export const projectKeys = {
  detail: (projectId: number) => ["projects", projectId] as const,
  reviews: (submissionId: number) =>
    ["projects", "reviews", submissionId] as const,
};

// ── useProject: single project detail ────────────────────────────────

export function useProject(projectId: number) {
  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => projectsApi.getProject(projectId),
    enabled: projectId > 0,
  });
}

// ── useSubmitProject: submit project work ────────────────────────────

export function useSubmitProject(projectId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { description: string; files: File[] }) =>
      projectsApi.submitProject(projectId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      });
    },
  });
}

// ── useSubmitReview: submit a review for a submission ─────────────────

export function useSubmitReview(submissionId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { scores: Record<string, number>; feedback: string }) =>
      projectsApi.submitReview(submissionId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: projectKeys.reviews(submissionId),
      });
    },
  });
}

// ── useReviews: get reviews for a submission ─────────────────────────

export function useReviews(submissionId: number) {
  return useQuery({
    queryKey: projectKeys.reviews(submissionId),
    queryFn: () => projectsApi.getReviews(submissionId),
    enabled: submissionId > 0,
  });
}
