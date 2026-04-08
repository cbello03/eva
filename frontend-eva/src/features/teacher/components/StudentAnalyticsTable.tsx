"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  IconButton,
  LinearProgress,
  Box,
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import Link from "next/link";
import type { StudentListItem } from "../types";

interface StudentAnalyticsTableProps {
  students: StudentListItem[];
  courseId: number;
}

export default function StudentAnalyticsTable({
  students,
  courseId,
}: StudentAnalyticsTableProps) {
  if (students.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No students enrolled yet.
      </Typography>
    );
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small" aria-label="Student analytics">
        <TableHead>
          <TableRow>
            <TableCell>Student</TableCell>
            <TableCell>Progress</TableCell>
            <TableCell align="right">Score</TableCell>
            <TableCell align="right">Streak</TableCell>
            <TableCell align="right">Last Active</TableCell>
            <TableCell align="right">Details</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {students.map((student) => (
            <TableRow key={student.id}>
              <TableCell>{student.display_name}</TableCell>
              <TableCell>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={student.progress_percentage}
                    sx={{ flex: 1, minWidth: 60 }}
                  />
                  <Typography variant="caption">
                    {Math.round(student.progress_percentage)}%
                  </Typography>
                </Box>
              </TableCell>
              <TableCell align="right">
                {Math.round(student.current_score)}%
              </TableCell>
              <TableCell align="right">{student.streak_count}</TableCell>
              <TableCell align="right">
                {student.last_activity_date
                  ? new Date(student.last_activity_date).toLocaleDateString()
                  : "—"}
              </TableCell>
              <TableCell align="right">
                <IconButton
                  component={Link}
                  href={`/teacher/analytics/${courseId}/students/${student.id}`}
                  size="small"
                  aria-label={`View details for ${student.display_name}`}
                >
                  <VisibilityIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
