"use client";

import { Suspense } from "react";
import { Alert, Box, Container, Link as MuiLink, Typography } from "@mui/material";
import { LoginForm } from "@/features/auth/components";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

function RegistrationAlert() {
  const searchParams = useSearchParams();
  const justRegistered = searchParams.get("registered") === "true";

  if (!justRegistered) return null;

  return (
    <Alert severity="success" sx={{ width: "100%", mb: 2 }}>
      Cuenta creada exitosamente. Por favor, inicia sesión.
    </Alert>
  );
}

export default function LoginPage() {
  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          mt: 8,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <Typography component="h1" variant="h4" sx={{ mb: 1 }}>
          Bienvenido de nuevo
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Inicia sesión para continuar aprendiendo
        </Typography>

        <Suspense>
          <RegistrationAlert />
        </Suspense>

        <Box sx={{ width: "100%" }}>
          <LoginForm />
        </Box>

        <Typography variant="body2" sx={{ mt: 3 }}>
          ¿No tienes una cuenta?{" "}
          <MuiLink component={Link} href="/register">
            Registrarse
          </MuiLink>
        </Typography>
      </Box>
    </Container>
  );
}
