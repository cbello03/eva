import { useQuery } from "@tanstack/react-query";
import * as progressApi from "./api";

// ── Query keys ───────────────────────────────────────────────────────

export const progressKeys = {
  dashboard: ["progress", "dashboard"] as const,
  course: (courseId: number) => ["progress", "course", courseId] as const,
  heatmap: ["progress", "heatmap"] as const,
  mastery: ["progress", "mastery"] as const,
};

// ── useProgressDashboard ─────────────────────────────────────────────

export function useProgressDashboard() {
  return useQuery({
    queryKey: progressKeys.dashboard,
    queryFn: progressApi.getDashboard,
  });
}

// ── useCourseProgress ────────────────────────────────────────────────

export function useCourseProgress(courseId: number) {
  return useQuery({
    queryKey: progressKeys.course(courseId),
    queryFn: () => progressApi.getCourseProgress(courseId),
    enabled: courseId > 0,
  });
}

// ── useActivityHeatmap ───────────────────────────────────────────────

export function useActivityHeatmap() {
  return useQuery({
    queryKey: progressKeys.heatmap,
    queryFn: progressApi.getActivityHeatmap,
  });
}

// ── useMasteryScores ─────────────────────────────────────────────────

export function useMasteryScores() {
  return useQuery({
    queryKey: progressKeys.mastery,
    queryFn: progressApi.getMasteryScores,
  });
}
