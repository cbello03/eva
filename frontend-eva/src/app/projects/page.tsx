"use client";

import {
  Container,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Grid,
} from "@mui/material";
import { Schedule as ScheduleIcon } from "@mui/icons-material";
import Link from "next/link";
import { useEnrollments } from "@/features/courses/hooks";

export default function ProjectsPage() {
  const { data: enrollments, isLoading, error } = useEnrollments();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Projects
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        View and submit projects from your enrolled courses.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load projects.
        </Alert>
      )}

      {isLoading ? (
        <Box sx={{ textAlign: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      ) : !enrollments || enrollments.length === 0 ? (
        <Alert severity="info">
          Enroll in a course to see available projects.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {enrollments
            .filter((e) => e.is_active)
            .map((enrollment) => (
              <Grid key={enrollment.id} size={{ xs: 12, sm: 6, md: 4 }}>
                <Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" gutterBottom>
                      {enrollment.course_title}
                    </Typography>
                    <Chip
                      icon={<ScheduleIcon />}
                      label={`${Math.round(enrollment.progress_percentage)}% complete`}
                      size="small"
                      variant="outlined"
                    />
                  </CardContent>
                  <CardActions sx={{ px: 2, pb: 2 }}>
                    <Button
                      component={Link}
                      href={`/courses/${enrollment.course_id}`}
                      size="small"
                      variant="outlined"
                      fullWidth
                    >
                      View Course Projects
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
        </Grid>
      )}
    </Container>
  );
}
