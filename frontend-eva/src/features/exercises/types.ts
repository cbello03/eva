export type ExerciseType = 'multiple_choice' | 'fill_blank' | 'matching' | 'free_text';

export interface Exercise {
  id: number;
  exercise_type: ExerciseType;
  question_text: string;
  config: any; // El JSON que varía según el tipo
}

export interface LessonSession {
  lesson_id: number;
  current_exercise_index: number;
  is_completed: boolean;
  total_exercises: number;
  current_exercise?: Exercise;
}

export interface AnswerResult {
  is_correct: boolean;
  correct_answer?: any;
  feedback?: string;
}