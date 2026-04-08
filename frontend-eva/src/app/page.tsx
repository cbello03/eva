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
          Aprende mejor, en comunidad
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: 560 }}>
          EVA combina lecciones interactivas, gamificación y aprendizaje social
          en una sola plataforma. Avanza a tu propio ritmo.
        </Typography>

        <Stack direction="row" spacing={2}>
          <Button
            component={Link}
            href="/register"
            variant="contained"
            size="large"
          >
            Comenzar
          </Button>
          <Button
            component={Link}
            href="/login"
            variant="outlined"
            size="large"
          >
            Iniciar sesión
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
          title="Lecciones interactivas"
          description="Ejercicios con retroalimentación instantánea y mecánicas de reintento."
        />
        <FeatureCard
          icon={<EmojiEvents fontSize="large" color="secondary" />}
          title="XP y logros"
          description="Gana puntos, sube de nivel, mantén tu racha y escala en la tabla de posiciones."
        />
        <FeatureCard
          icon={<Group fontSize="large" color="primary" />}
          title="Aprendizaje social"
          description="Foros, chat en tiempo real y proyectos colaborativos con compañeros."
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
