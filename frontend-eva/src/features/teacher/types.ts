/** TypeScript types for the teacher feature, matching backend schemas. */

export interface TeacherCourseListItem {
  id: number;
  title: string;
  status: "draft" | "published";
  enrollment_count: number;
  updated_at: string;
}

export interface CourseAnalytics {
  course_id: number;
  total_enrolled: number;
  average_completion: number;
  average_score: number;
  average_time_per_lesson: number;
}

export interface StudentListItem {
  id: number;
  display_name: string;
  email: string;
  progress_percentage: number;
  current_score: number;
  streak_count: number;
  last_activity_date: string | null;
}

export interface StudentDetail {
  id: number;
  display_name: string;
  email: string;
  units: StudentUnitProgress[];
}

export interface StudentUnitProgress {
  unit_id: number;
  title: string;
  lessons: StudentLessonProgress[];
}

export interface StudentLessonProgress {
  lesson_id: number;
  title: string;
  is_completed: boolean;
  score: number;
}

export interface HeatmapCell {
  exercise_id: number;
  topic: string;
  accuracy: number;
  total_attempts: number;
}
