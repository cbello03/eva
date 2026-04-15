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
        Aún no hay estudiantes inscritos.
      </Typography>
    );
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small" aria-label="Analíticas de estudiantes">
        <TableHead>
          <TableRow>
            <TableCell>Estudiante</TableCell>
            <TableCell>Progreso</TableCell>
            <TableCell align="right">Puntuación</TableCell>
            <TableCell align="right">Racha</TableCell>
            <TableCell align="right">Última actividad</TableCell>
            <TableCell align="right">Detalles</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {students.map((student, index) => (
            <TableRow key={`${student.id}-${student.email}-${index}`}>
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
                  aria-label={`Ver detalles de ${student.display_name}`}
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
