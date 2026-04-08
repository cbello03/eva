"use client";

import { Box, Container, Link as MuiLink, Typography } from "@mui/material";
import { RegisterForm } from "@/features/auth/components";
import Link from "next/link";

export default function RegisterPage() {
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
          Create your account
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Start your learning journey on EVA
        </Typography>

        <Box sx={{ width: "100%" }}>
          <RegisterForm />
        </Box>

        <Typography variant="body2" sx={{ mt: 3 }}>
          Already have an account?{" "}
          <MuiLink component={Link} href="/login">
            Log in
          </MuiLink>
        </Typography>
      </Box>
    </Container>
  );
}
