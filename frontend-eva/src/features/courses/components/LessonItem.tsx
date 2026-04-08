"use client";

import Link from "next/link";
import {
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";
import {
  PlayCircle as PlayIcon,
  Lock as LockIcon,
} from "@mui/icons-material";
import type { Lesson } from "../types";

interface LessonItemProps {
  lesson: Lesson;
  courseId: number;
  isEnrolled: boolean;
}

export default function LessonItem({
  lesson,
  courseId,
  isEnrolled,
}: LessonItemProps) {
  if (!isEnrolled) {
    return (
      <ListItem disablePadding>
        <ListItemButton disabled>
          <ListItemIcon sx={{ minWidth: 36 }}>
            <LockIcon fontSize="small" color="disabled" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Typography variant="body2" color="text.secondary">
                {lesson.order}. {lesson.title}
              </Typography>
            }
          />
        </ListItemButton>
      </ListItem>
    );
  }

  return (
    <ListItem disablePadding>
      <ListItemButton
        component={Link}
        href={`/courses/${courseId}/lessons/${lesson.id}`}
      >
        <ListItemIcon sx={{ minWidth: 36 }}>
          <PlayIcon fontSize="small" color="primary" />
        </ListItemIcon>
        <ListItemText
          primary={
            <Typography variant="body2">
              {lesson.order}. {lesson.title}
            </Typography>
          }
        />
      </ListItemButton>
    </ListItem>
  );
}
