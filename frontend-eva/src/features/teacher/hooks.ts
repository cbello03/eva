import { useQuery } from "@tanstack/react-query";
import * as teacherApi from "./api";

// ── Query keys ───────────────────────────────────────────────────────

export const teacherKeys = {
  analytics: (courseId: number) =>
    ["teacher", "analytics", courseId] as const,
  students: (courseId: number) =>
    ["teacher", "students", courseId] as const,
  studentDetail: (courseId: number, studentId: number) =>
    ["teacher", "students", courseId, studentId] as const,
  heatmap: (courseId: number) =>
    ["teacher", "heatmap", courseId] as const,
};

// ── useCourseAnalytics ───────────────────────────────────────────────

export function useCourseAnalytics(courseId: number) {
  return useQuery({
    queryKey: teacherKeys.analytics(courseId),
    queryFn: () => teacherApi.getCourseAnalytics(courseId),
    enabled: courseId > 0,
  });
}

// ── useStudentList ───────────────────────────────────────────────────

export function useStudentList(courseId: number) {
  return useQuery({
    queryKey: teacherKeys.students(courseId),
    queryFn: () => teacherApi.getStudentList(courseId),
    enabled: courseId > 0,
  });
}

// ── useStudentDetail ─────────────────────────────────────────────────

export function useStudentDetail(courseId: number, studentId: number) {
  return useQuery({
    queryKey: teacherKeys.studentDetail(courseId, studentId),
    queryFn: () => teacherApi.getStudentDetail(courseId, studentId),
    enabled: courseId > 0 && studentId > 0,
  });
}

// ── useHeatmap ───────────────────────────────────────────────────────

export function useHeatmap(courseId: number) {
  return useQuery({
    queryKey: teacherKeys.heatmap(courseId),
    queryFn: () => teacherApi.getHeatmap(courseId),
    enabled: courseId > 0,
  });
}
