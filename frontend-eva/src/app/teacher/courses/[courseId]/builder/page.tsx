"use client";

import { use, useState, useCallback } from "react";
import {
  Container,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Grid,
  Divider,
} from "@mui/material";
import { useCourse } from "@/features/courses/hooks";
import { useQueryClient } from "@tanstack/react-query";
import { courseKeys } from "@/features/courses/hooks";
import { apiClient } from "@/lib/api-client";
import CourseTree from "@/features/teacher/components/CourseTree";
import ExerciseForm from "@/features/teacher/components/ExerciseForm";
import PublishButton from "@/features/teacher/components/PublishButton";

interface PageProps {
  params: Promise<{ courseId: string }>;
}

export default function CourseBuilderPage({ params }: PageProps) {
  const { courseId: courseIdStr } = use(params);
  const courseId = Number(courseIdStr);
  const queryClient = useQueryClient();

  const { data: course, isLoading, error } = useCourse(courseId);
  const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const invalidateCourse = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: courseKeys.detail(courseId) });
  }, [queryClient, courseId]);

  const handleAddUnit = useCallback(
    async (title: string) => {
      await apiClient.post(`/courses/${courseId}/units`, { title });
      invalidateCourse();
    },
    [courseId, invalidateCourse],
  );

  const handleAddLesson = useCallback(
    async (unitId: number, title: string) => {
      await apiClient.post(`/units/${unitId}/lessons`, { title });
      invalidateCourse();
    },
    [invalidateCourse],
  );

  const handleAddExercise = useCallback(
    async (data: {
      question_text: string;
      exercise_type: string;
      config: Record<string, unknown>;
      difficulty: number;
      topic: string;
    }) => {
      if (!selectedLessonId) return;
      setSubmitting(true);
      try {
        await apiClient.post(`/lessons/${selectedLessonId}/exercises`, data);
        invalidateCourse();
      } finally {
        setSubmitting(false);
      }
    },
    [selectedLessonId, invalidateCourse],
  );

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error || !course) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Error al cargar el curso.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h4" component="h1">
          {course.title}
        </Typography>
        <PublishButton
          courseId={courseId}
          status={course.status}
          onPublished={invalidateCourse}
        />
      </Box>

      <Divider sx={{ mb: 3 }} />

      <Grid container spacing={3}>
        {/* Course tree */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="h6" gutterBottom>
            Estructura del curso
          </Typography>
          <CourseTree
            units={course.units}
            onAddUnit={handleAddUnit}
            onAddLesson={handleAddLesson}
            onSelectLesson={setSelectedLessonId}
          />
        </Grid>

        {/* Exercise form */}
        <Grid size={{ xs: 12, md: 6 }}>
          {selectedLessonId ? (
            <>
              <Typography variant="h6" gutterBottom>
                Agregar ejercicio a la lección
              </Typography>
              <ExerciseForm
                onSubmit={handleAddExercise}
                isSubmitting={submitting}
              />
            </>
          ) : (
            <Box sx={{ py: 4, textAlign: "center" }}>
              <Typography variant="body2" color="text.secondary">
                Selecciona una lección del árbol para agregar ejercicios.
              </Typography>
            </Box>
          )}
        </Grid>
      </Grid>
    </Container>
  );
}
