"use client";

import { useMemo } from "react";
import { Box, Typography, Tooltip } from "@mui/material";
import type { ActivityDay } from "../types";

interface ActivityHeatmapProps {
  data: ActivityDay[];
}

/** Map activity intensity to a color. */
function getColor(lessonsCompleted: number): string {
  if (lessonsCompleted === 0) return "var(--mui-palette-action-hover, #ebedf0)";
  if (lessonsCompleted <= 1) return "#9be9a8";
  if (lessonsCompleted <= 3) return "#40c463";
  if (lessonsCompleted <= 5) return "#30a14e";
  return "#216e39";
}

const CELL_SIZE = 14;
const CELL_GAP = 2;
const DAYS_IN_WEEK = 7;
const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];

export default function ActivityHeatmap({ data }: ActivityHeatmapProps) {
  const { grid, weeks } = useMemo(() => {
    // Build a map of date → activity
    const activityMap = new Map<string, ActivityDay>();
    for (const day of data) {
      activityMap.set(day.date, day);
    }

    // Generate 90 days ending today
    const today = new Date();
    const days: Array<{ date: string; activity: ActivityDay | undefined }> = [];
    for (let i = 89; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().split("T")[0]!;
      days.push({ date: dateStr, activity: activityMap.get(dateStr) });
    }

    // Pad start so first day aligns to correct weekday
    const firstDate = new Date(days[0]!.date);
    const startPad = firstDate.getDay(); // 0=Sun
    const padded = [
      ...Array.from<null>({ length: startPad }).fill(null),
      ...days,
    ];

    // Group into weeks (columns)
    const weekCount = Math.ceil(padded.length / DAYS_IN_WEEK);
    return { grid: padded, weeks: weekCount };
  }, [data]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Activity (Last 90 Days)
      </Typography>
      <Box sx={{ display: "flex", gap: `${CELL_GAP}px`, overflow: "auto" }}>
        {/* Day labels */}
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: `${CELL_GAP}px`,
            mr: 0.5,
          }}
        >
          {DAY_LABELS.map((label, i) => (
            <Typography
              key={i}
              variant="caption"
              sx={{
                height: CELL_SIZE,
                lineHeight: `${CELL_SIZE}px`,
                fontSize: 10,
                color: "text.secondary",
              }}
            >
              {label}
            </Typography>
          ))}
        </Box>

        {/* Heatmap grid */}
        {Array.from({ length: weeks }).map((_, weekIdx) => (
          <Box
            key={weekIdx}
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: `${CELL_GAP}px`,
            }}
          >
            {Array.from({ length: DAYS_IN_WEEK }).map((_, dayIdx) => {
              const idx = weekIdx * DAYS_IN_WEEK + dayIdx;
              const cell = grid[idx];
              if (!cell) {
                return (
                  <Box
                    key={dayIdx}
                    sx={{
                      width: CELL_SIZE,
                      height: CELL_SIZE,
                      borderRadius: 0.5,
                    }}
                  />
                );
              }
              const lessons = cell.activity?.lessons_completed ?? 0;
              const xp = cell.activity?.xp_earned ?? 0;
              return (
                <Tooltip
                  key={dayIdx}
                  title={`${cell.date}: ${lessons} lesson${lessons !== 1 ? "s" : ""}, ${xp} XP`}
                >
                  <Box
                    sx={{
                      width: CELL_SIZE,
                      height: CELL_SIZE,
                      borderRadius: 0.5,
                      bgcolor: getColor(lessons),
                      cursor: "default",
                    }}
                    role="img"
                    aria-label={`${cell.date}: ${lessons} lessons completed`}
                  />
                </Tooltip>
              );
            })}
          </Box>
        ))}
      </Box>
    </Box>
  );
}
