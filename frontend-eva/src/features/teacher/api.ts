import { apiClient } from "@/lib/api-client";
import type {
  CourseAnalytics,
  StudentListItem,
  StudentDetail,
  HeatmapCell,
} from "./types";

/** Get aggregate analytics for a course. */
export async function getCourseAnalytics(
  courseId: number,
): Promise<CourseAnalytics> {
  const response = await apiClient.get<CourseAnalytics>(
    `/teacher/courses/${courseId}/analytics`,
  );
  return response.data;
}

/** Get the student list with progress for a course. */
export async function getStudentList(
  courseId: number,
): Promise<StudentListItem[]> {
  const response = await apiClient.get<StudentListItem[]>(
    `/teacher/courses/${courseId}/students`,
  );
  return response.data;
}

/** Get detailed progress for a specific student in a course. */
export async function getStudentDetail(
  courseId: number,
  studentId: number,
): Promise<StudentDetail> {
  const response = await apiClient.get<StudentDetail>(
    `/teacher/courses/${courseId}/students/${studentId}`,
  );
  return response.data;
}

/** Get exercise accuracy heatmap data for a course. */
export async function getHeatmap(courseId: number): Promise<HeatmapCell[]> {
  const response = await apiClient.get<HeatmapCell[]>(
    `/teacher/courses/${courseId}/heatmap`,
  );
  return response.data;
}
