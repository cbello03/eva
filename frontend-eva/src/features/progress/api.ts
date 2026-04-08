import { apiClient } from "@/lib/api-client";
import type {
  ProgressDashboard,
  CourseProgress,
  ActivityDay,
  MasteryScore,
} from "./types";

/** Get overall student progress dashboard stats. */
export async function getDashboard(): Promise<ProgressDashboard> {
  const response = await apiClient.get<ProgressDashboard>(
    "/progress/dashboard",
  );
  return response.data;
}

/** Get detailed progress for a specific course. */
export async function getCourseProgress(
  courseId: number,
): Promise<CourseProgress> {
  const response = await apiClient.get<CourseProgress>(
    `/progress/courses/${courseId}`,
  );
  return response.data;
}

/** Get activity heatmap data (default 90 days). */
export async function getActivityHeatmap(): Promise<ActivityDay[]> {
  const response = await apiClient.get<ActivityDay[]>("/progress/activity");
  return response.data;
}

/** Get topic mastery scores. */
export async function getMasteryScores(): Promise<MasteryScore[]> {
  const response = await apiClient.get<MasteryScore[]>("/progress/mastery");
  return response.data;
}
