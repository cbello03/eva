import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/features/auth/store";
import * as exercisesApi from "./api";
import type { AnswerSubmission } from "./types";

// ── Query keys ───────────────────────────────────────────────────────

export const exerciseKeys = {
  session: (lessonId: number) => ["exercises", "session", lessonId] as const,
};

// ── useLessonSession: start or resume a lesson player session ────────

export function useLessonSession(lessonId: number) {
  const { isAuthenticated, user } = useAuthStore();
  const isStudent = user?.role === "student";

  return useQuery({
    queryKey: exerciseKeys.session(lessonId),
    queryFn: async () => {
      try {
        return await exercisesApi.resumeLesson(lessonId);
      } catch {
        return await exercisesApi.startLesson(lessonId);
      }
    },
    enabled: isAuthenticated && isStudent && lessonId > 0,
    staleTime: 0, // Always refetch to get latest session state
  });
}

// ── useSubmitAnswer: submit an answer and refresh session ────────────

export function useSubmitAnswer(lessonId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      exerciseId,
      data,
    }: {
      exerciseId: number;
      data: AnswerSubmission;
    }) => exercisesApi.submitAnswer(exerciseId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: exerciseKeys.session(lessonId),
      });
    },
  });
}
