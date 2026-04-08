"use client";

import { useState } from "react";
import {
  Box,
  Typography,
  IconButton,
  TextField,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Button,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import FolderIcon from "@mui/icons-material/Folder";
import ArticleIcon from "@mui/icons-material/Article";
import QuizIcon from "@mui/icons-material/Quiz";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import type { Unit, Lesson } from "@/features/courses/types";

interface Exercise {
  id: number;
  question_text: string;
  exercise_type: string;
  order: number;
}

interface LessonWithExercises extends Lesson {
  exercises?: Exercise[];
}

interface UnitWithLessons extends Omit<Unit, "lessons"> {
  lessons: LessonWithExercises[];
}

interface CourseTreeProps {
  units: UnitWithLessons[];
  onAddUnit: (title: string) => void;
  onAddLesson: (unitId: number, title: string) => void;
  onSelectLesson: (lessonId: number) => void;
  onDeleteUnit?: (unitId: number) => void;
  onDeleteLesson?: (lessonId: number) => void;
}

export default function CourseTree({
  units,
  onAddUnit,
  onAddLesson,
  onSelectLesson,
  onDeleteUnit,
  onDeleteLesson,
}: CourseTreeProps) {
  const [expandedUnits, setExpandedUnits] = useState<Set<number>>(
    new Set(units.map((u) => u.id)),
  );
  const [newUnitTitle, setNewUnitTitle] = useState("");
  const [addingLessonTo, setAddingLessonTo] = useState<number | null>(null);
  const [newLessonTitle, setNewLessonTitle] = useState("");

  const toggleUnit = (unitId: number) => {
    setExpandedUnits((prev) => {
      const next = new Set(prev);
      if (next.has(unitId)) next.delete(unitId);
      else next.add(unitId);
      return next;
    });
  };

  const handleAddUnit = () => {
    const title = newUnitTitle.trim();
    if (!title) return;
    onAddUnit(title);
    setNewUnitTitle("");
  };

  const handleAddLesson = (unitId: number) => {
    const title = newLessonTitle.trim();
    if (!title) return;
    onAddLesson(unitId, title);
    setNewLessonTitle("");
    setAddingLessonTo(null);
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <List disablePadding>
        {units.map((unit) => (
          <Box key={unit.id}>
            <ListItem
              secondaryAction={
                onDeleteUnit && (
                  <IconButton
                    size="small"
                    onClick={() => onDeleteUnit(unit.id)}
                    aria-label={`Delete unit ${unit.title}`}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                )
              }
            >
              <IconButton size="small" onClick={() => toggleUnit(unit.id)}>
                {expandedUnits.has(unit.id) ? (
                  <ExpandLessIcon />
                ) : (
                  <ExpandMoreIcon />
                )}
              </IconButton>
              <ListItemIcon sx={{ minWidth: 36 }}>
                <FolderIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary={unit.title}
                secondary={`${unit.lessons.length} lesson(s)`}
              />
            </ListItem>

            <Collapse in={expandedUnits.has(unit.id)}>
              <List disablePadding sx={{ pl: 4 }}>
                {unit.lessons.map((lesson) => (
                  <Box key={lesson.id}>
                    <ListItem
                      component="div"
                      sx={{ cursor: "pointer" }}
                      onClick={() => onSelectLesson(lesson.id)}
                      secondaryAction={
                        onDeleteLesson && (
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteLesson(lesson.id);
                            }}
                            aria-label={`Delete lesson ${lesson.title}`}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        )
                      }
                    >
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <ArticleIcon color="action" />
                      </ListItemIcon>
                      <ListItemText
                        primary={lesson.title}
                        secondary={
                          lesson.exercises
                            ? `${lesson.exercises.length} exercise(s)`
                            : undefined
                        }
                      />
                    </ListItem>

                    {/* Exercise list under lesson */}
                    {lesson.exercises && lesson.exercises.length > 0 && (
                      <List disablePadding sx={{ pl: 4 }}>
                        {lesson.exercises.map((ex) => (
                          <ListItem key={ex.id} dense>
                            <ListItemIcon sx={{ minWidth: 32 }}>
                              <QuizIcon fontSize="small" color="disabled" />
                            </ListItemIcon>
                            <ListItemText
                              primary={ex.question_text}
                              secondary={ex.exercise_type}
                              slotProps={{ primary: { variant: "body2" } }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    )}
                  </Box>
                ))}

                {/* Add lesson */}
                {addingLessonTo === unit.id ? (
                  <ListItem>
                    <TextField
                      size="small"
                      placeholder="Lesson title"
                      value={newLessonTitle}
                      onChange={(e) => setNewLessonTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleAddLesson(unit.id);
                        if (e.key === "Escape") setAddingLessonTo(null);
                      }}
                      autoFocus
                      sx={{ mr: 1 }}
                    />
                    <Button
                      size="small"
                      onClick={() => handleAddLesson(unit.id)}
                    >
                      Add
                    </Button>
                  </ListItem>
                ) : (
                  <ListItem>
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => {
                        setAddingLessonTo(unit.id);
                        setNewLessonTitle("");
                      }}
                    >
                      Add Lesson
                    </Button>
                  </ListItem>
                )}
              </List>
            </Collapse>
          </Box>
        ))}
      </List>

      {/* Add unit */}
      <Box sx={{ display: "flex", gap: 1, mt: 1, alignItems: "center" }}>
        <TextField
          size="small"
          placeholder="New unit title"
          value={newUnitTitle}
          onChange={(e) => setNewUnitTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleAddUnit();
          }}
        />
        <Button size="small" startIcon={<AddIcon />} onClick={handleAddUnit}>
          Add Unit
        </Button>
      </Box>
    </Paper>
  );
}
