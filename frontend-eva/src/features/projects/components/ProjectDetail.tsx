"use client";

import {
  Paper,
  Typography,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import {
  Schedule as ScheduleIcon,
  Group as GroupIcon,
} from "@mui/icons-material";
import type { Project } from "../api";

interface ProjectDetailProps {
  project: Project;
}

export default function ProjectDetail({ project }: ProjectDetailProps) {
  const isOverdue = new Date(project.submission_deadline) < new Date();

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        {project.title}
      </Typography>

      <Typography variant="body1" sx={{ mb: 2 }}>
        {project.description}
      </Typography>

      <Box sx={{ display: "flex", gap: 1, mb: 3, flexWrap: "wrap" }}>
        <Chip
          icon={<ScheduleIcon />}
          label={`Fecha límite: ${new Date(project.submission_deadline).toLocaleDateString()}`}
          color={isOverdue ? "error" : "default"}
          size="small"
          variant="outlined"
        />
        {project.peer_review_enabled && (
          <Chip
            icon={<GroupIcon />}
            label={`Revisión por pares (${project.peer_reviewers_count} revisores)`}
            size="small"
            variant="outlined"
          />
        )}
      </Box>

      {project.rubric.length > 0 && (
        <>
          <Typography variant="h6" gutterBottom>
            Rúbrica
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Criterio</TableCell>
                <TableCell>Descripción</TableCell>
                <TableCell align="right">Puntuación máxima</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {project.rubric.map((criterion) => (
                <TableRow key={criterion.name}>
                  <TableCell sx={{ fontWeight: 600 }}>{criterion.name}</TableCell>
                  <TableCell>{criterion.description}</TableCell>
                  <TableCell align="right">{criterion.max_score}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}
    </Paper>
  );
}
