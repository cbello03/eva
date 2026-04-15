import { apiClient } from "@/lib/api-client";
import type {
  CourseAnalytics,
  StudentListItem,
  StudentDetail,
  HeatmapCell,
} from "./types";

interface CourseAnalyticsApi {
  course_id: number;
  total_enrolled: number;
  average_completion_rate: number;
  average_score: number;
  average_time_per_lesson: number;
}

interface StudentListItemApi {
  student_id: number;
  display_name: string;
  email: string;
  progress_percentage: number;
  score: number;
  streak: number;
  last_activity: string | null;
}

interface HeatmapCellApi {
  topic: string;
  total_answers: number;
  correct_answers: number;
  accuracy: number;
}

/** Get aggregate analytics for a course. */
export async function getCourseAnalytics(
  courseId: number,
): Promise<CourseAnalytics> {
  const response = await apiClient.get<CourseAnalyticsApi>(
    `/teacher/courses/${courseId}/analytics`,
  );
  return {
    course_id: response.data.course_id,
    total_enrolled: response.data.total_enrolled,
    average_completion: response.data.average_completion_rate,
    average_score: response.data.average_score,
    average_time_per_lesson: response.data.average_time_per_lesson,
  };
}

/** Get the student list with progress for a course. */
export async function getStudentList(
  courseId: number,
): Promise<StudentListItem[]> {
  const response = await apiClient.get<StudentListItemApi[]>(
    `/teacher/courses/${courseId}/students`,
  );
  return response.data.map((student) => ({
    id: student.student_id,
    display_name: student.display_name,
    email: student.email,
    progress_percentage: student.progress_percentage,
    current_score: student.score,
    streak_count: student.streak,
    last_activity_date: student.last_activity,
  }));
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
  const response = await apiClient.get<HeatmapCellApi[]>(
    `/teacher/courses/${courseId}/heatmap`,
  );
  return response.data.map((cell, index) => ({
    exercise_id: index + 1,
    topic: cell.topic,
    accuracy: cell.accuracy,
    total_attempts: cell.total_answers,
  }));
}
