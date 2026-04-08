"use client";

import { use, useCallback, useState } from "react";
import {
  Container,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
  Chip,
} from "@mui/material";
import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import Link from "next/link";
import { useLessonSession, useSubmitAnswer } from "@/features/exercises/hooks";
import type { AnswerResult, Exercise } from "@/features/exercises/types";
import ProgressBar from "@/features/exercises/components/ProgressBar";
import FeedbackIndicator from "@/features/exercises/components/FeedbackIndicator";
import LessonComplete from "@/features/exercises/components/LessonComplete";
import MultipleChoiceExercise from "@/features/exercises/components/MultipleChoiceExercise";
import FillBlankExercise from "@/features/exercises/components/FillBlankExercise";
import MatchingExercise from "@/features/exercises/components/MatchingExercise";
import FreeTextExercise from "@/features/exercises/components/FreeTextExercise";

interface LessonPlayerPageProps {
  params: Promise<{ courseId: string; lessonId: string }>;
}

export default function LessonPlayerPage({ params }: LessonPlayerPageProps) {
  const { courseId: courseIdStr, lessonId: lessonIdStr } = use(params);
  const courseId = Number(courseIdStr);
  const lessonId = Number(lessonIdStr);

  const {
    data: session,
    isLoading,
    error,
  } = useLessonSession(lessonId);
  const submitMutation = useSubmitAnswer(lessonId);

  const [feedback, setFeedback] = useState<AnswerResult | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const handleSubmit = useCallback(
    (answer: Record<string, unknown>) => {
      if (!session?.current_exercise) return;

      submitMutation.mutate(
        {
          exerciseId: session.current_exercise.id,
          data: { answer },
        },
        {
          onSuccess: (result) => {
            setFeedback(result);
            setShowFeedback(true);

            // Auto-advance after showing feedback
            setTimeout(() => {
              setShowFeedback(false);
              setFeedback(null);
            }, 2000);
          },
        },
      );
    },
    [session?.current_exercise, submitMutation],
  );

  if (isLoading) {
    return (
      <Container maxWidth="sm" sx={{ py: 4, textAlign: "center" }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Cargando lección…
        </Typography>
      </Container>
    );
  }

  if (error || !session) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Error al cargar la lección. Es posible que no estés inscrito en este curso.
        </Alert>
        <Button
          component={Link}
          href={`/courses/${courseId}`}
          startIcon={<ArrowBackIcon />}
        >
          Volver al curso
        </Button>
      </Container>
    );
  }

  // Lesson completed
  if (session.is_completed) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <LessonComplete
          correctFirstAttempt={session.correct_first_attempt}
          totalExercises={session.total_exercises}
          courseId={courseId}
        />
      </Container>
    );
  }

  const exercise = session.current_exercise;
  const isSubmitting = submitMutation.isPending || showFeedback;

  // Calculate completed count from progress percentage and total
  const completedCount =
    session.total_exercises > 0
      ? Math.round(
          (session.progress_percentage / 100) * session.total_exercises,
        )
      : 0;

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Button
          component={Link}
          href={`/courses/${courseId}`}
          startIcon={<ArrowBackIcon />}
          size="small"
        >
          Salir de la lección
        </Button>
        {session.retry_queue_size > 0 && (
          <Chip
            label={`${session.retry_queue_size} por reintentar`}
            size="small"
            color="warning"
            variant="outlined"
          />
        )}
      </Box>

      <ProgressBar
        current={completedCount}
        total={session.total_exercises}
      />

      {exercise ? (
        <>
          <ExerciseRenderer
            exercise={exercise}
            disabled={isSubmitting}
            onSubmit={handleSubmit}
          />
          <FeedbackIndicator result={feedback} visible={showFeedback} />
          {submitMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Error al enviar la respuesta. Por favor, inténtalo de nuevo.
            </Alert>
          )}
        </>
      ) : (
        <Alert severity="info">
          No hay más ejercicios disponibles. La sesión debería completarse en breve.
        </Alert>
      )}
    </Container>
  );
}

// ── Exercise renderer — delegates to the correct component ───────────

function ExerciseRenderer({
  exercise,
  disabled,
  onSubmit,
}: {
  exercise: Exercise;
  disabled: boolean;
  onSubmit: (answer: Record<string, unknown>) => void;
}) {
  switch (exercise.exercise_type) {
    case "multiple_choice":
      return (
        <MultipleChoiceExercise
          key={exercise.id}
          questionText={exercise.question_text}
          config={exercise.config as import("@/features/exercises/types").MultipleChoiceConfig}
          disabled={disabled}
          onSubmit={onSubmit}
        />
      );
    case "fill_blank":
      return (
        <FillBlankExercise
          key={exercise.id}
          questionText={exercise.question_text}
          disabled={disabled}
          onSubmit={onSubmit}
        />
      );
    case "matching":
      return (
        <MatchingExercise
          key={exercise.id}
          questionText={exercise.question_text}
          config={exercise.config as import("@/features/exercises/types").MatchingConfig}
          disabled={disabled}
          onSubmit={onSubmit}
        />
      );
    case "free_text":
      return (
        <FreeTextExercise
          key={exercise.id}
          questionText={exercise.question_text}
          disabled={disabled}
          onSubmit={onSubmit}
        />
      );
    default:
      return (
        <Alert severity="warning">
          Tipo de ejercicio desconocido: {exercise.exercise_type}
        </Alert>
      );
  }
}
