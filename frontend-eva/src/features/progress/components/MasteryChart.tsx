"use client";

import {
  Box,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
} from "@mui/material";
import type { MasteryScore } from "../types";

interface MasteryChartProps {
  scores: MasteryScore[];
}

function getMasteryColor(
  score: number,
): "success" | "warning" | "error" | "info" {
  if (score >= 0.8) return "success";
  if (score >= 0.6) return "info";
  if (score >= 0.4) return "warning";
  return "error";
}

export default function MasteryChart({ scores }: MasteryChartProps) {
  const sorted = [...scores].sort((a, b) => b.mastery_score - a.mastery_score);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Dominio por tema
      </Typography>
      {sorted.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          Aún no hay datos de dominio. Completa algunos ejercicios para ver tu progreso.
        </Typography>
      ) : (
        <List disablePadding>
          {sorted.map((score) => {
            const pct = Math.round(score.mastery_score * 100);
            return (
              <ListItem key={score.topic} disableGutters sx={{ py: 1 }}>
                <ListItemText
                  primary={
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        mb: 0.5,
                      }}
                    >
                      <Typography variant="body2">{score.topic}</Typography>
                      <Chip
                        label={`${pct}%`}
                        size="small"
                        color={getMasteryColor(score.mastery_score)}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <LinearProgress
                      variant="determinate"
                      value={pct}
                      color={getMasteryColor(score.mastery_score)}
                      sx={{ height: 6, borderRadius: 3 }}
                      aria-label={`${score.topic}: ${pct}% dominio`}
                    />
                  }
                  disableTypography
                />
              </ListItem>
            );
          })}
        </List>
      )}
    </Box>
  );
}
