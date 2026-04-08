/** TypeScript types for the courses feature, matching backend schemas. */

export interface Lesson {
  id: number;
  title: string;
  order: number;
}

export interface Unit {
  id: number;
  title: string;
  order: number;
  lessons: Lesson[];
}

export interface Course {
  id: number;
  title: string;
  description: string;
  teacher_id: number;
  status: "draft" | "published";
  published_at: string | null;
  created_at: string;
  updated_at: string;
  units: Unit[];
}

export interface CourseListItem {
  id: number;
  title: string;
  description: string;
  teacher_id: number;
  status: "draft" | "published";
  published_at: string | null;
  created_at: string;
}

export interface Enrollment {
  id: number;
  course_id: number;
  course_title: string;
  is_active: boolean;
  enrolled_at: string;
  progress_percentage: number;
}
