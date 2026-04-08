"use client";

import { useState } from "react";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  ToggleButtonGroup,
  ToggleButton,
  Typography,
  CircularProgress,
  Alert,
  Chip,
} from "@mui/material";
import { useLeaderboard } from "../hooks";
import type { LeaderboardPeriod } from "../types";

export default function LeaderboardTable() {
  const [period, setPeriod] = useState<LeaderboardPeriod>("weekly");
  const { data, isLoading, error } = useLeaderboard(period);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h6">Leaderboard</Typography>
        <ToggleButtonGroup
          value={period}
          exclusive
          onChange={(_, v: LeaderboardPeriod | null) => {
            if (v) setPeriod(v);
          }}
          size="small"
        >
          <ToggleButton value="weekly">Weekly</ToggleButton>
          <ToggleButton value="alltime">All Time</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load leaderboard.
        </Alert>
      )}

      {isLoading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      ) : data ? (
        <>
          {data.user_rank != null && (
            <Chip
              label={`Your rank: #${data.user_rank} · ${data.user_xp.toLocaleString()} XP`}
              color="primary"
              variant="outlined"
              size="small"
              sx={{ mb: 1 }}
            />
          )}
          <TableContainer component={Paper} variant="outlined">
            <Table size="small" aria-label="Leaderboard">
              <TableHead>
                <TableRow>
                  <TableCell width={60}>Rank</TableCell>
                  <TableCell>Student</TableCell>
                  <TableCell align="right">XP</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.entries.map((entry) => (
                  <TableRow
                    key={entry.student_id}
                    sx={
                      data.user_rank === entry.rank
                        ? { bgcolor: "action.selected" }
                        : undefined
                    }
                  >
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: entry.rank <= 3 ? 700 : 400 }}>
                        #{entry.rank}
                      </Typography>
                    </TableCell>
                    <TableCell>{entry.display_name}</TableCell>
                    <TableCell align="right">
                      {entry.total_xp.toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
                {data.entries.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No entries yet.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      ) : null}
    </Box>
  );
}
