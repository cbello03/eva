"use client";

import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import type { CourseProgress } from "../types";

interface CourseProgressDetailProps {
  progress: CourseProgress;
}

export default function CourseProgressDetail({
  progress,
}: CourseProgressDetailProps) {
  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
        <Typography variant="h6">{progress.course_title}</Typography>
        <Chip
          label={`${Math.round(progress.completion_percentage)}%`}
          color={progress.completion_percentage >= 100 ? "success" : "default"}
          size="small"
        />
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(progress.completion_percentage, 100)}
        sx={{ height: 8, borderRadius: 4, mb: 1 }}
        aria-label={`${Math.round(progress.completion_percentage)}% completado`}
      />
      <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: "block" }}>
        {progress.lessons_completed} / {progress.total_lessons} lecciones
        completadas · Puntuación: {Math.round(progress.total_score)}%
      </Typography>

      {progress.units.map((unit) => (
        <Accordion key={unit.unit_id} variant="outlined" disableGutters>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2">{unit.unit_title}</Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 0 }}>
            <List dense disablePadding>
              {unit.lessons.map((lesson) => (
                <ListItem key={lesson.lesson_id}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {lesson.is_completed ? (
                      <CheckCircleIcon color="success" fontSize="small" />
                    ) : (
                      <RadioButtonUncheckedIcon
                        color="disabled"
                        fontSize="small"
                      />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={lesson.lesson_title}
                    secondary={
                      lesson.is_completed
                        ? `Puntuación: ${Math.round(lesson.score)}%`
                        : "No completada"
                    }
                  />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
