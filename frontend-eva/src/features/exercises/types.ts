/** TypeScript types for the exercises feature, matching backend schemas. */

// ── Exercise types ───────────────────────────────────────────────────

export type ExerciseType =
  | "multiple_choice"
  | "fill_blank"
  | "matching"
  | "free_text";

export interface MatchingPair {
  left: string;
  right: string;
}

export interface MultipleChoiceOption {
  id: number | string;
  text: string;
}

export interface MultipleChoiceConfig {
  options: Array<string | MultipleChoiceOption>;
  correct_index: number;
}

export interface FillBlankConfig {
  blank_position: number;
  accepted_answers: string[];
}

export interface MatchingConfig {
  pairs: MatchingPair[];
}

export interface FreeTextConfig {
  model_answer: string;
  rubric: string;
}

export type ExerciseConfig =
  | MultipleChoiceConfig
  | FillBlankConfig
  | MatchingConfig
  | FreeTextConfig;

export interface Exercise {
  id: number;
  exercise_type: ExerciseType;
  question_text: string;
  order: number;
  config: ExerciseConfig;
  difficulty: number;
  topic: string;
  is_collaborative: boolean;
  collab_group_size: number | null;
}

// ── Lesson session ───────────────────────────────────────────────────

export interface LessonSession {
  id: number;
  lesson_id: number;
  current_exercise: Exercise | null;
  progress_percentage: number;
  is_completed: boolean;
  correct_first_attempt: number;
  total_exercises: number;
  retry_queue_size: number;
}

// ── Answer submission ────────────────────────────────────────────────

export interface AnswerSubmission {
  answer: Record<string, unknown>;
}

export interface AnswerResult {
  is_correct: boolean;
  correct_answer: Record<string, unknown> | null;
  feedback: string;
}
