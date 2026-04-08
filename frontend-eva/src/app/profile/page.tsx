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
import {
  useGamificationProfile,
  useAchievements,
  useXPHistory,
} from "@/features/gamification/hooks";
import { useUser } from "@/features/auth/hooks";
import XPDisplay from "@/features/gamification/components/XPDisplay";
import StreakDisplay from "@/features/gamification/components/StreakDisplay";
import AchievementGrid from "@/features/gamification/components/AchievementGrid";

export default function ProfilePage() {
  const { data: user } = useUser();
  const {
    data: profile,
    isLoading: profileLoading,
    error: profileError,
  } = useGamificationProfile();
  const {
    data: achievements,
    isLoading: achievementsLoading,
  } = useAchievements();
  const { data: xpHistory } = useXPHistory();

  const isLoading = profileLoading || achievementsLoading;

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
        <Alert severity="error">Error al cargar los datos del perfil.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {user?.display_name ?? "Perfil"}
      </Typography>

      {/* Stats cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6 }}>
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

        <Grid size={{ xs: 12, sm: 6 }}>
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
      </Grid>

      <Divider sx={{ mb: 3 }} />

      {/* Achievements */}
      <Typography variant="h6" gutterBottom>
        Logros
      </Typography>
      {achievements && <AchievementGrid achievements={achievements} />}

      <Divider sx={{ my: 3 }} />

      {/* Recent XP History */}
      <Typography variant="h6" gutterBottom>
        Actividad de XP reciente
      </Typography>
      {xpHistory && xpHistory.length > 0 ? (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {xpHistory.slice(0, 10).map((tx) => (
            <Card key={tx.id} variant="outlined">
              <CardContent
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  py: 1,
                  "&:last-child": { pb: 1 },
                }}
              >
                <Box>
                  <Typography variant="body2">
                    {tx.source_type.replace(/_/g, " ")}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(tx.timestamp).toLocaleDateString()}
                  </Typography>
                </Box>
                <Typography variant="body2" color="primary" sx={{ fontWeight: 600 }}>
                  +{tx.amount} XP
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary">
          Sin actividad de XP aún.
        </Typography>
      )}
    </Container>
  );
}
