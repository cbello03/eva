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
  status: 'draft' | 'published';
  units?: Unit[];
}

export interface Enrollment {
  id: number;
  course_id: number;
  is_active: boolean;
  completion_percentage: number;
}