/** TypeScript types for the gamification feature, matching backend schemas. */

// ── Gamification profile ─────────────────────────────────────────────

export interface GamificationProfile {
  total_xp: number;
  current_level: number;
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
}

// ── XP transactions ──────────────────────────────────────────────────

export interface XPTransaction {
  id: number;
  amount: number;
  source_type: string;
  source_id: number;
  timestamp: string;
}

// ── Achievements ─────────────────────────────────────────────────────

export interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  condition_type: string;
  condition_value: number;
  is_unlocked: boolean;
  unlocked_at: string | null;
  current_progress: number;
}

// ── Streak ───────────────────────────────────────────────────────────

export interface Streak {
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
}

// ── Leaderboard ──────────────────────────────────────────────────────

export interface LeaderboardEntry {
  rank: number;
  student_id: number;
  display_name: string;
  total_xp: number;
}

export interface Leaderboard {
  period: string;
  entries: LeaderboardEntry[];
  user_rank: number | null;
  user_xp: number;
}

export type LeaderboardPeriod = "weekly" | "alltime";
