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
      Account created successfully. Please log in.
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
          Welcome back
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Log in to continue learning
        </Typography>

        <Suspense>
          <RegistrationAlert />
        </Suspense>

        <Box sx={{ width: "100%" }}>
          <LoginForm />
        </Box>

        <Typography variant="body2" sx={{ mt: 3 }}>
          Don&apos;t have an account?{" "}
          <MuiLink component={Link} href="/register">
            Sign up
          </MuiLink>
        </Typography>
      </Box>
    </Container>
  );
}
