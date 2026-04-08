"use client";

import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  List,
  Chip,
  Box,
} from "@mui/material";
import { ExpandMore as ExpandMoreIcon } from "@mui/icons-material";
import type { Unit } from "../types";
import LessonItem from "./LessonItem";

interface UnitAccordionProps {
  unit: Unit;
  courseId: number;
  isEnrolled: boolean;
  defaultExpanded?: boolean;
}

export default function UnitAccordion({
  unit,
  courseId,
  isEnrolled,
  defaultExpanded = false,
}: UnitAccordionProps) {
  return (
    <Accordion defaultExpanded={defaultExpanded} disableGutters>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, width: "100%" }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            Unit {unit.order}: {unit.title}
          </Typography>
          <Chip
            label={`${unit.lessons.length} lesson${unit.lessons.length !== 1 ? "s" : ""}`}
            size="small"
            variant="outlined"
            sx={{ ml: "auto", mr: 1 }}
          />
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 0 }}>
        <List disablePadding>
          {unit.lessons.map((lesson) => (
            <LessonItem
              key={lesson.id}
              lesson={lesson}
              courseId={courseId}
              isEnrolled={isEnrolled}
            />
          ))}
          {unit.lessons.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
              No lessons in this unit yet.
            </Typography>
          )}
        </List>
      </AccordionDetails>
    </Accordion>
  );
}
