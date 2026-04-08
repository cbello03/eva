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
} from "@mui/icons-material";
import Link from "next/link";
import { useCourse, useEnrollments, useEnroll, useUnenroll } from "@/features/courses/hooks";
import UnitAccordion from "@/features/courses/components/UnitAccordion";

interface CourseDetailPageProps {
  params: Promise<{ courseId: string }>;
}

export default function CourseDetailPage({ params }: CourseDetailPageProps) {
  const { courseId: courseIdStr } = use(params);
  const courseId = Number(courseIdStr);

  const { data: course, isLoading, error } = useCourse(courseId);
  const { data: enrollments } = useEnrollments();
  const enrollMutation = useEnroll();
  const unenrollMutation = useUnenroll();

  const enrollment = enrollments?.find(
    (e) => e.course_id === courseId && e.is_active,
  );
  const isEnrolled = Boolean(enrollment);
  const progress = enrollment?.progress_percentage ?? 0;

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
        <Alert severity="error">Failed to load course.</Alert>
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
        Back to Courses
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
                label={`${course.units.length} unit${course.units.length !== 1 ? "s" : ""}`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`${totalLessons} lesson${totalLessons !== 1 ? "s" : ""}`}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>

          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 1 }}>
            {isEnrolled ? (
              <>
                <Box sx={{ width: 200 }}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Progress
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
                  {unenrollMutation.isPending ? "Unenrolling…" : "Unenroll"}
                </Button>
              </>
            ) : (
              <Button
                variant="contained"
                startIcon={<EnrollIcon />}
                onClick={handleEnroll}
                disabled={enrollMutation.isPending}
              >
                {enrollMutation.isPending ? "Enrolling…" : "Enroll in Course"}
              </Button>
            )}
          </Box>
        </Box>
      </Paper>

      {enrollMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to enroll. You may already be enrolled in this course.
        </Alert>
      )}

      <Typography variant="h5" component="h2" gutterBottom>
        Course Content
      </Typography>

      {course.units.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          This course has no content yet.
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
