"use client";

import {
  Box,
  Typography,
  LinearProgress,
  Chip,
} from "@mui/material";
import StarIcon from "@mui/icons-material/Star";

interface XPDisplayProps {
  totalXP: number;
  currentLevel: number;
}

/**
 * Calculate XP thresholds for a given level.
 * Uses a quadratic progression: threshold(n) = 100 * n^2.
 */
function getLevelThreshold(level: number): number {
  return 100 * level * level;
}

export default function XPDisplay({ totalXP, currentLevel }: XPDisplayProps) {
  const currentThreshold = getLevelThreshold(currentLevel);
  const nextThreshold = getLevelThreshold(currentLevel + 1);
  const xpInLevel = totalXP - currentThreshold;
  const xpNeeded = nextThreshold - currentThreshold;
  const progress = xpNeeded > 0 ? Math.min((xpInLevel / xpNeeded) * 100, 100) : 100;

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
        <Chip
          icon={<StarIcon />}
          label={`Nivel ${currentLevel}`}
          color="primary"
          size="small"
        />
        <Typography variant="body2" color="text.secondary">
          {totalXP.toLocaleString()} XP
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{ height: 8, borderRadius: 4 }}
        aria-label={`${Math.round(progress)}% para el siguiente nivel`}
      />
      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
        {xpInLevel.toLocaleString()} / {xpNeeded.toLocaleString()} XP para Nivel{" "}
        {currentLevel + 1}
      </Typography>
    </Box>
  );
}
