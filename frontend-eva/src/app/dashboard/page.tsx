"use client";

import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Box,
  CircularProgress,
  Alert,
  Divider,
} from "@mui/material";
import SchoolIcon from "@mui/icons-material/School";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import { useGamificationProfile } from "@/features/gamification/hooks";
import { useEnrollments } from "@/features/courses/hooks";
import XPDisplay from "@/features/gamification/components/XPDisplay";
import StreakDisplay from "@/features/gamification/components/StreakDisplay";
import LeaderboardTable from "@/features/gamification/components/LeaderboardTable";

export default function DashboardPage() {
  const {
    data: profile,
    isLoading: profileLoading,
    error: profileError,
  } = useGamificationProfile();
  const {
    data: enrollments,
    isLoading: enrollmentsLoading,
  } = useEnrollments();

  const isLoading = profileLoading || enrollmentsLoading;

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (profileError) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Error al cargar los datos del panel.</Alert>
      </Container>
    );
  }

  const activeEnrollments = (enrollments ?? []).filter((e) => e.is_active);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Panel
      </Typography>

      {/* Stats row */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                XP y Nivel
              </Typography>
              {profile && (
                <XPDisplay
                  totalXP={profile.total_xp}
                  currentLevel={profile.current_level}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Racha
              </Typography>
              {profile && (
                <StreakDisplay
                  currentStreak={profile.current_streak}
                  longestStreak={profile.longest_streak}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Cursos
              </Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 1 }}>
                <SchoolIcon color="primary" />
                <Typography variant="h6">
                  {activeEnrollments.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  inscrito
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Divider sx={{ mb: 3 }} />

      <Grid container spacing={3}>
        {/* Enrolled courses */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="h6" gutterBottom>
            Cursos inscritos
          </Typography>
          {activeEnrollments.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              Aún no te has inscrito en ningún curso.
            </Typography>
          ) : (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
              {activeEnrollments.map((enrollment) => (
                <Card key={enrollment.id} variant="outlined">
                  <CardContent
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 2,
                      py: 1.5,
                      "&:last-child": { pb: 1.5 },
                    }}
                  >
                    <MenuBookIcon color="action" />
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="body2" sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {enrollment.course_title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {Math.round(enrollment.progress_percentage)}% completado
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Grid>

        {/* Leaderboard */}
        <Grid size={{ xs: 12, md: 6 }}>
          <LeaderboardTable />
        </Grid>
      </Grid>
    </Container>
  );
}
