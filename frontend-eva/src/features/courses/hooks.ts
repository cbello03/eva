import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useAuthStore } from "@/features/auth/store";
import * as coursesApi from "./api";

// ── Query keys ───────────────────────────────────────────────────────

export const courseKeys = {
  all: ["courses"] as const,
  detail: (courseId: number) => ["courses", courseId] as const,
  enrollments: ["enrollments"] as const,
};

// ── useCourses: list courses visible to the user ─────────────────────

export function useCourses() {
  return useQuery({
    queryKey: courseKeys.all,
    queryFn: coursesApi.listCourses,
  });
}

// ── useCourse: single course with unit/lesson hierarchy ──────────────

export function useCourse(courseId: number) {
  return useQuery({
    queryKey: courseKeys.detail(courseId),
    queryFn: () => coursesApi.getCourse(courseId),
    enabled: courseId > 0,
  });
}

// ── useEnrollments: student's enrolled courses with progress ─────────

export function useEnrollments() {
  const { isAuthenticated, user } = useAuthStore();
  const isStudent = user?.role === "student";

  return useQuery({
    queryKey: courseKeys.enrollments,
    queryFn: coursesApi.listEnrollments,
    enabled: isAuthenticated && isStudent,
  });
}

// ── useEnroll: enroll in a course ────────────────────────────────────

export function useEnroll() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: coursesApi.enrollInCourse,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: courseKeys.enrollments });
      void queryClient.invalidateQueries({ queryKey: courseKeys.all });
    },
  });
}

// ── useUnenroll: unenroll from a course ──────────────────────────────

export function useUnenroll() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: coursesApi.unenrollFromCourse,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: courseKeys.enrollments });
      void queryClient.invalidateQueries({ queryKey: courseKeys.all });
    },
  });
}
