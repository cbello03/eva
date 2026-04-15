"use client";

import { use } from "react";
import {
  Container,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
  Paper,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  PersonAdd as EnrollIcon,
  PersonRemove as UnenrollIcon,
  Forum as ForumIcon,
  Chat as ChatIcon,
} from "@mui/icons-material";
import Link from "next/link";
import { useCourse, useEnrollments, useEnroll, useUnenroll } from "@/features/courses/hooks";
import { useAuth } from "@/features/auth/hooks";
import UnitAccordion from "@/features/courses/components/UnitAccordion";

interface CourseDetailPageProps {
  params: Promise<{ courseId: string }>;
}

export default function CourseDetailPage({ params }: CourseDetailPageProps) {
  const { courseId: courseIdStr } = use(params);
  const courseId = Number(courseIdStr);
  const { user } = useAuth();
  const isStudent = user?.role === "student";
  const isTeacherOrAdmin = user?.role === "teacher" || user?.role === "admin";

  const { data: course, isLoading, error } = useCourse(courseId);
  const { data: enrollments } = useEnrollments();
  const enrollMutation = useEnroll();
  const unenrollMutation = useUnenroll();

  const enrollment = enrollments?.find(
    (e) => e.course_id === courseId && e.is_active,
  );
  const isEnrolled = Boolean(enrollment);
  const progress = enrollment?.progress_percentage ?? 0;
  const canAccessSocial = isEnrolled || isTeacherOrAdmin;

  const handleEnroll = () => enrollMutation.mutate(courseId);
  const handleUnenroll = () => unenrollMutation.mutate(courseId);

  if (isLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: "center" }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !course) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">Error al cargar el curso.</Alert>
      </Container>
    );
  }

  const totalLessons = course.units.reduce((sum, u) => sum + u.lessons.length, 0);

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Button
        component={Link}
        href="/courses"
        startIcon={<ArrowBackIcon />}
        sx={{ mb: 2 }}
      >
        Volver a Cursos
      </Button>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="h1" gutterBottom>
              {course.title}
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              {course.description}
            </Typography>
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              <Chip
                label={`${course.units.length} unidad${course.units.length !== 1 ? "es" : ""}`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`${totalLessons} lección${totalLessons !== 1 ? "es" : ""}`}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>

          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 1 }}>
            {isStudent && isEnrolled ? (
              <>
                <Box sx={{ width: 200 }}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Progreso
                    </Typography>
                    <Typography variant="caption" sx={{ fontWeight: 600 }}>
                      {Math.round(progress)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={progress}
                    sx={{ borderRadius: 4, height: 8 }}
                  />
                </Box>
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  startIcon={<UnenrollIcon />}
                  onClick={handleUnenroll}
                  disabled={unenrollMutation.isPending}
                >
                  {unenrollMutation.isPending ? "Desinscribiendo…" : "Desinscribirse"}
                </Button>
              </>
            ) : isStudent ? (
              <Button
                variant="contained"
                startIcon={<EnrollIcon />}
                onClick={handleEnroll}
                disabled={enrollMutation.isPending}
              >
                {enrollMutation.isPending ? "Inscribiendo…" : "Inscribirse en el curso"}
              </Button>
            ) : (
              <Alert severity="info" sx={{ maxWidth: 320 }}>
                Vista de profesor: la inscripcion y reproduccion de lecciones es solo para estudiantes.
              </Alert>
            )}
          </Box>
        </Box>
      </Paper>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
          Comunidad del curso
        </Typography>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          <Button
            component={Link}
            href={`/courses/${courseId}/forum`}
            startIcon={<ForumIcon />}
            variant="outlined"
            size="small"
            disabled={!canAccessSocial}
          >
            Foro
          </Button>
          <Button
            component={Link}
            href={`/courses/${courseId}/chat`}
            startIcon={<ChatIcon />}
            variant="outlined"
            size="small"
            disabled={!canAccessSocial}
          >
            Chat en vivo
          </Button>
        </Box>
        {!canAccessSocial && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
            Inscribete al curso para acceder al foro y al chat.
          </Typography>
        )}
      </Paper>

      {enrollMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Error al inscribirse. Es posible que ya estés inscrito en este curso.
        </Alert>
      )}

      <Typography variant="h5" component="h2" gutterBottom>
        Contenido del curso
      </Typography>

      {course.units.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          Este curso aún no tiene contenido.
        </Typography>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {course.units.map((unit, index) => (
            <UnitAccordion
              key={unit.id}
              unit={unit}
              courseId={courseId}
              isEnrolled={isEnrolled}
              defaultExpanded={index === 0}
            />
          ))}
        </Box>
      )}
    </Container>
  );
}
