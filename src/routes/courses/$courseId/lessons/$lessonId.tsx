import React, { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Box, Typography, CircularProgress, Alert, Button, Container } from '@mui/material';
import { useStartLesson, useSubmitAnswer } from '../../../../features/exercises/hooks';
import { ProgressBar } from '../../../../features/exercises/components/ProgressBar';
import { MultipleChoiceExercise } from '../../../../features/exercises/components/MultipleChoiceExercise';
// import { FillBlankExercise } from '../../../../features/exercises/components/FillBlankExercise';
// import { MatchingExercise } from '../../../../features/exercises/components/MatchingExercise';

export const Route = createFileRoute('/courses/$courseId/lessons/$lessonId')({
  component: LessonPlayer,
});

function LessonPlayer() {
  const { lessonId } = Route.useParams();
  const { data: session, isLoading, error } = useStartLesson(lessonId);
  const submitMutation = useSubmitAnswer(lessonId);
  const [feedback, setFeedback] = useState<{ isCorrect: boolean; message?: string } | null>(null);

  if (isLoading) return <Box display="flex" justifyContent="center" mt={10}><CircularProgress /></Box>;
  if (error || !session) return <Alert severity="error">Error al cargar la lección.</Alert>;

  // Pantalla de Lección Completada [cite: 1687]
  if (session.is_completed) {
    return (
      <Container maxWidth="sm" sx={{ textAlign: 'center', mt: 10 }}>
        <Typography variant="h3" gutterBottom>¡Lección Completada!</Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Has ganado puntos de experiencia.
        </Typography>
        <Button variant="contained" size="large" onClick={() => window.history.back()}>
          Volver al Curso
        </Button>
      </Container>
    );
  }

  const currentExercise = session.current_exercise;
  if (!currentExercise) return <Alert severity="warning">No hay ejercicios disponibles.</Alert>;

  const handleAnswerSubmit = (answerData: any) => {
    setFeedback(null); // Limpiar feedback previo
    
    submitMutation.mutate(
      { exerciseId: currentExercise.id, answer: answerData },
      {
        onSuccess: (result) => {
          // Mostrar feedback (ej. animación o alerta) basándose en result.is_correct
          setFeedback({
            isCorrect: result.is_correct,
            message: result.is_correct ? '¡Correcto! Excelente trabajo.' : `Incorrecto. ${result.feedback || ''}`,
          });

          // Si es correcto, el hook automáticamente recargará la sesión y traerá el siguiente ejercicio
        },
      }
    );
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      {/* Barra de progreso  */}
      <ProgressBar currentIndex={session.current_exercise_index} total={session.total_exercises} />

      {/* Alerta temporal para el feedback visual [cite: 1680, 1686] */}
      {feedback && (
        <Alert severity={feedback.isCorrect ? 'success' : 'error'} sx={{ mb: 3 }}>
          {feedback.message}
        </Alert>
      )}

      {/* Renderizado condicional según el tipo de ejercicio */}
      <Box sx={{ minHeight: 400 }}>
        {currentExercise.exercise_type === 'multiple_choice' && (
          <MultipleChoiceExercise 
            exercise={currentExercise} 
            onSubmit={handleAnswerSubmit} 
            isSubmitting={submitMutation.isPending}
          />
        )}
        {/* Aquí agregaríamos los otros tipos de ejercicios más adelante */}
        {currentExercise.exercise_type !== 'multiple_choice' && (
          <Typography color="text.secondary">
            Tipo de ejercicio "{currentExercise.exercise_type}" en construcción.
          </Typography>
        )}
      </Box>
    </Container>
  );
}