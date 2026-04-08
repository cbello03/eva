"use client";

import {
  Box,
  Typography,
  Tooltip,
  Paper,
} from "@mui/material";
import type { HeatmapCell } from "../types";

interface PerformanceHeatmapProps {
  cells: HeatmapCell[];
}

function getColor(accuracy: number): string {
  if (accuracy >= 0.8) return "#4caf50";
  if (accuracy >= 0.6) return "#8bc34a";
  if (accuracy >= 0.4) return "#ffeb3b";
  if (accuracy >= 0.2) return "#ff9800";
  return "#f44336";
}

export default function PerformanceHeatmap({ cells }: PerformanceHeatmapProps) {
  if (cells.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No performance data available yet.
      </Typography>
    );
  }

  // Group by topic
  const topics = [...new Set(cells.map((c) => c.topic))];

  return (
    <Paper variant="outlined" sx={{ p: 2, overflowX: "auto" }}>
      {topics.map((topic) => {
        const topicCells = cells.filter((c) => c.topic === topic);
        return (
          <Box key={topic} sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: "block" }}>
              {topic}
            </Typography>
            <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
              {topicCells.map((cell) => (
                <Tooltip
                  key={cell.exercise_id}
                  title={`Exercise #${cell.exercise_id}: ${Math.round(cell.accuracy * 100)}% accuracy (${cell.total_attempts} attempts)`}
                >
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      borderRadius: 0.5,
                      bgcolor: getColor(cell.accuracy),
                      cursor: "pointer",
                    }}
                  />
                </Tooltip>
              ))}
            </Box>
          </Box>
        );
      })}

      {/* Legend */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 2 }}>
        <Typography variant="caption" color="text.secondary">Low</Typography>
        {[0.1, 0.3, 0.5, 0.7, 0.9].map((v) => (
          <Box
            key={v}
            sx={{ width: 16, height: 16, borderRadius: 0.5, bgcolor: getColor(v) }}
          />
        ))}
        <Typography variant="caption" color="text.secondary">High</Typography>
      </Box>
    </Paper>
  );
}
