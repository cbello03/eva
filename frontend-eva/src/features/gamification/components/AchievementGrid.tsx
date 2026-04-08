"use client";

import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Tooltip,
  Grid,
} from "@mui/material";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import LockIcon from "@mui/icons-material/Lock";
import type { Achievement } from "../types";

interface AchievementGridProps {
  achievements: Achievement[];
}

export default function AchievementGrid({
  achievements,
}: AchievementGridProps) {
  const earned = achievements.filter((a) => a.is_unlocked);
  const locked = achievements.filter((a) => !a.is_unlocked);

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Obtenidos ({earned.length})
      </Typography>
      <Grid container spacing={1.5} sx={{ mb: 3 }}>
        {earned.map((a) => (
          <Grid key={a.id} size={{ xs: 6, sm: 4, md: 3 }}>
            <AchievementCard achievement={a} />
          </Grid>
        ))}
        {earned.length === 0 && (
          <Grid size={12}>
            <Typography variant="body2" color="text.secondary">
              Aún no has obtenido logros. ¡Sigue aprendiendo!
            </Typography>
          </Grid>
        )}
      </Grid>

      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Bloqueados ({locked.length})
      </Typography>
      <Grid container spacing={1.5}>
        {locked.map((a) => (
          <Grid key={a.id} size={{ xs: 6, sm: 4, md: 3 }}>
            <AchievementCard achievement={a} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}


function AchievementCard({ achievement }: { achievement: Achievement }) {
  const progress =
    achievement.condition_value > 0
      ? Math.min(
          (achievement.current_progress / achievement.condition_value) * 100,
          100,
        )
      : 0;

  return (
    <Tooltip
      title={
        achievement.is_unlocked
          ? `Desbloqueado: ${achievement.description}`
          : `${achievement.current_progress}/${achievement.condition_value} — ${achievement.description}`
      }
    >
      <Card
        variant="outlined"
        sx={{
          opacity: achievement.is_unlocked ? 1 : 0.6,
          textAlign: "center",
          py: 1.5,
          px: 1,
        }}
      >
        <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
          {achievement.is_unlocked ? (
            <EmojiEventsIcon color="warning" sx={{ fontSize: 32 }} />
          ) : (
            <LockIcon color="disabled" sx={{ fontSize: 32 }} />
          )}
          <Typography variant="caption" sx={{ mt: 0.5, display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {achievement.name}
          </Typography>
          {!achievement.is_unlocked && (
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ mt: 0.5, height: 4, borderRadius: 2 }}
              aria-label={`${Math.round(progress)}% progreso`}
            />
          )}
        </CardContent>
      </Card>
    </Tooltip>
  );
}
