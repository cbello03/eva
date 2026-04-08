"use client";

import { use } from "react";
import {
  Container,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  Divider,
} from "@mui/material";
import PeopleIcon from "@mui/icons-material/People";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ScoreIcon from "@mui/icons-material/Score";
import TimerIcon from "@mui/icons-material/Timer";
import { useCourseAnalytics, useStudentList, useHeatmap } from "@/features/teacher/hooks";
import StudentAnalyticsTable from "@/features/teacher/components/StudentAnalyticsTable";
import PerformanceHeatmap from "@/features/teacher/components/PerformanceHeatmap";

interface PageProps {
  params: Promise<{ courseId: string }>;
}

export default function CourseAnalyticsPage({ params }: PageProps) {
  const { courseId: courseIdStr } = use(params);
  const courseId = Number(courseIdStr);

  const {
    data: analytics,
    isLoading: analyticsLoading,
    error: analyticsError,
  } = useCourseAnalytics(courseId);
  const { data: students, isLoading: studentsLoading } =
    useStudentList(courseId);
  const { data: heatmap, isLoading: heatmapLoading } = useHeatmap(courseId);

  const isLoading = analyticsLoading || studentsLoading || heatmapLoading;

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (analyticsError) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Error al cargar las analíticas.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Analíticas del curso
      </Typography>

      {/* Aggregate stats */}
      {analytics && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 6, md: 3 }}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <PeopleIcon color="primary" />
                  <Typography variant="overline" color="text.secondary">
                    Inscritos
                  </Typography>
                </Box>
                <Typography variant="h5">{analytics.total_enrolled}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, md: 3 }}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <TrendingUpIcon color="primary" />
                  <Typography variant="overline" color="text.secondary">
                    Completado promedio
                  </Typography>
                </Box>
                <Typography variant="h5">
                  {Math.round(analytics.average_completion)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, md: 3 }}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <ScoreIcon color="primary" />
                  <Typography variant="overline" color="text.secondary">
                    Puntuación promedio
                  </Typography>
                </Box>
                <Typography variant="h5">
                  {Math.round(analytics.average_score)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, md: 3 }}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <TimerIcon color="primary" />
                  <Typography variant="overline" color="text.secondary">
                    Tiempo promedio/Lección
                  </Typography>
                </Box>
                <Typography variant="h5">
                  {Math.round(analytics.average_time_per_lesson)}m
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Divider sx={{ mb: 3 }} />

      {/* Student list */}
      <Typography variant="h6" gutterBottom>
        Estudiantes
      </Typography>
      <StudentAnalyticsTable
        students={students ?? []}
        courseId={courseId}
      />

      <Divider sx={{ my: 3 }} />

      {/* Performance heatmap */}
      <Typography variant="h6" gutterBottom>
        Mapa de rendimiento
      </Typography>
      <PerformanceHeatmap cells={heatmap ?? []} />
    </Container>
  );
}
