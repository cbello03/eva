"use client";

import { Grid, Card, CardContent, Typography, Box } from "@mui/material";
import StarIcon from "@mui/icons-material/Star";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import SchoolIcon from "@mui/icons-material/School";
import type { ProgressDashboard } from "../types";

interface ProgressOverviewProps {
  dashboard: ProgressDashboard;
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}

function StatCard({ icon, label, value }: StatCardProps) {
  return (
    <Card variant="outlined">
      <CardContent sx={{ display: "flex", alignItems: "center", gap: 2 }}>
        {icon}
        <Box>
          <Typography variant="h6">{value}</Typography>
          <Typography variant="caption" color="text.secondary">
            {label}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function ProgressOverview({
  dashboard,
}: ProgressOverviewProps) {
  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 6, sm: 3 }}>
        <StatCard
          icon={<StarIcon color="primary" />}
          label="XP Total"
          value={dashboard.total_xp.toLocaleString()}
        />
      </Grid>
      <Grid size={{ xs: 6, sm: 3 }}>
        <StatCard
          icon={<StarIcon color="secondary" />}
          label="Nivel"
          value={dashboard.current_level}
        />
      </Grid>
      <Grid size={{ xs: 6, sm: 3 }}>
        <StatCard
          icon={<WhatshotIcon color="warning" />}
          label="Racha"
          value={`${dashboard.current_streak} días`}
        />
      </Grid>
      <Grid size={{ xs: 6, sm: 3 }}>
        <StatCard
          icon={<SchoolIcon color="info" />}
          label="Inscritos"
          value={dashboard.courses_enrolled}
        />
      </Grid>
    </Grid>
  );
}
