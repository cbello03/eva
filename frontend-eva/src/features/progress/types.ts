/** TypeScript types for the progress feature, matching backend schemas. */

// ── Dashboard ────────────────────────────────────────────────────────

export interface ProgressDashboard {
  total_xp: number;
  current_level: number;
  current_streak: number;
  courses_enrolled: number;
  courses_completed: number;
}

// ── Course progress ──────────────────────────────────────────────────

export interface LessonProgress {
  lesson_id: number;
  lesson_title: string;
  is_completed: boolean;
  score: number;
}

export interface UnitProgress {
  unit_id: number;
  unit_title: string;
  lessons: LessonProgress[];
}

export interface CourseProgress {
  course_id: number;
  course_title: string;
  completion_percentage: number;
  total_score: number;
  lessons_completed: number;
  total_lessons: number;
  units: UnitProgress[];
}

// ── Activity heatmap ─────────────────────────────────────────────────

export interface ActivityDay {
  date: string;
  lessons_completed: number;
  xp_earned: number;
  time_spent_minutes: number;
}

// ── Mastery scores ───────────────────────────────────────────────────

export interface MasteryScore {
  topic: string;
  correct_count: number;
  total_count: number;
  mastery_score: number;
  last_reviewed: string | null;
}
