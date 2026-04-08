import { apiClient } from "@/lib/api-client";
import type { AnswerResult, AnswerSubmission, LessonSession } from "./types";

/** Start a lesson player session. Creates or returns existing session. */
export async function startLesson(lessonId: number): Promise<LessonSession> {
  const response = await apiClient.get<LessonSession>(
    `/lessons/${lessonId}/start`,
  );
  return response.data;
}

/** Submit an answer to an exercise. */
export async function submitAnswer(
  exerciseId: number,
  data: AnswerSubmission,
): Promise<AnswerResult> {
  const response = await apiClient.post<AnswerResult>(
    `/exercises/${exerciseId}/submit`,
    data,
  );
  return response.data;
}

/** Resume an existing lesson session from saved progress. */
export async function resumeLesson(lessonId: number): Promise<LessonSession> {
  const response = await apiClient.get<LessonSession>(
    `/lessons/${lessonId}/resume`,
  );
  return response.data;
}
