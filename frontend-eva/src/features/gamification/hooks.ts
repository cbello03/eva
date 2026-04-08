import { useQuery } from "@tanstack/react-query";
import * as gamificationApi from "./api";
import type { LeaderboardPeriod } from "./types";

// ── Query keys ───────────────────────────────────────────────────────

export const gamificationKeys = {
  profile: ["gamification", "profile"] as const,
  leaderboard: (period: LeaderboardPeriod) =>
    ["gamification", "leaderboard", period] as const,
  achievements: ["gamification", "achievements"] as const,
  xpHistory: ["gamification", "xp-history"] as const,
};

// ── useGamificationProfile ───────────────────────────────────────────

export function useGamificationProfile() {
  return useQuery({
    queryKey: gamificationKeys.profile,
    queryFn: gamificationApi.getProfile,
  });
}

// ── useLeaderboard ───────────────────────────────────────────────────

export function useLeaderboard(period: LeaderboardPeriod = "weekly") {
  return useQuery({
    queryKey: gamificationKeys.leaderboard(period),
    queryFn: () => gamificationApi.getLeaderboard(period),
  });
}

// ── useAchievements ──────────────────────────────────────────────────

export function useAchievements() {
  return useQuery({
    queryKey: gamificationKeys.achievements,
    queryFn: gamificationApi.getAchievements,
  });
}

// ── useXPHistory ─────────────────────────────────────────────────────

export function useXPHistory() {
  return useQuery({
    queryKey: gamificationKeys.xpHistory,
    queryFn: gamificationApi.getXPHistory,
  });
}
