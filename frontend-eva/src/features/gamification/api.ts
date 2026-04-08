import { apiClient } from "@/lib/api-client";
import type {
  GamificationProfile,
  Leaderboard,
  LeaderboardPeriod,
  Achievement,
  XPTransaction,
} from "./types";

/** Get the current student's gamification profile (XP, level, streak). */
export async function getProfile(): Promise<GamificationProfile> {
  const response = await apiClient.get<GamificationProfile>(
    "/gamification/profile",
  );
  return response.data;
}

/** Get the leaderboard for a given period. */
export async function getLeaderboard(
  period: LeaderboardPeriod = "weekly",
): Promise<Leaderboard> {
  const response = await apiClient.get<Leaderboard>(
    "/gamification/leaderboard",
    { params: { period } },
  );
  return response.data;
}

/** Get all achievements with unlock status and progress. */
export async function getAchievements(): Promise<Achievement[]> {
  const response = await apiClient.get<Achievement[]>(
    "/gamification/achievements",
  );
  return response.data;
}

/** Get the student's XP transaction history. */
export async function getXPHistory(): Promise<XPTransaction[]> {
  const response = await apiClient.get<XPTransaction[]>(
    "/gamification/xp-history",
  );
  return response.data;
}
