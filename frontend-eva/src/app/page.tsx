"use client";

import Link from "next/link";
import { Box, Button, Container, Typography, Stack } from "@mui/material";
import { School, EmojiEvents, Group } from "@mui/icons-material";
import { useAuth } from "@/features/auth/hooks";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, router]);

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          mt: 12,
          mb: 8,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        <Typography variant="h2" component="h1" gutterBottom>
          Learn smarter, together
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: 560 }}>
          EVA combines interactive lessons, gamification, and social learning
          into one platform. Build skills at your own pace.
        </Typography>

        <Stack direction="row" spacing={2}>
          <Button
            component={Link}
            href="/register"
            variant="contained"
            size="large"
          >
            Get started
          </Button>
          <Button
            component={Link}
            href="/login"
            variant="outlined"
            size="large"
          >
            Log in
          </Button>
        </Stack>
      </Box>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={4}
        sx={{ mt: 4, mb: 8, justifyContent: "center", alignItems: "center" }}
      >
        <FeatureCard
          icon={<School fontSize="large" color="primary" />}
          title="Interactive lessons"
          description="Duolingo-style exercises with instant feedback and retry mechanics."
        />
        <FeatureCard
          icon={<EmojiEvents fontSize="large" color="secondary" />}
          title="XP & achievements"
          description="Earn points, level up, maintain streaks, and climb the leaderboard."
        />
        <FeatureCard
          icon={<Group fontSize="large" color="primary" />}
          title="Social learning"
          description="Forums, real-time chat, and collaborative projects with peers."
        />
      </Stack>
    </Container>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Box sx={{ textAlign: "center", flex: 1, maxWidth: 280 }}>
      <Box sx={{ mb: 1 }}>{icon}</Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
    </Box>
  );
}
