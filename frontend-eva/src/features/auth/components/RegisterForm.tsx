"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  LinearProgress,
  TextField,
  Typography,
} from "@mui/material";
import { useRegister } from "@/features/auth/hooks";
import {
  registerSchema,
  type RegisterFormData,
} from "@/features/auth/schemas";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { AxiosError } from "axios";

/** Calculate password strength 0–100 based on backend rules */
function getPasswordStrength(password: string): number {
  if (!password) return 0;
  let score = 0;
  if (password.length >= 8) score += 25;
  if (/[A-Z]/.test(password)) score += 25;
  if (/[a-z]/.test(password)) score += 25;
  if (/[0-9]/.test(password)) score += 25;
  return score;
}

function strengthColor(score: number): "error" | "warning" | "info" | "success" {
  if (score <= 25) return "error";
  if (score <= 50) return "warning";
  if (score <= 75) return "info";
  return "success";
}

function strengthLabel(score: number): string {
  if (score <= 25) return "Débil";
  if (score <= 50) return "Regular";
  if (score <= 75) return "Buena";
  return "Fuerte";
}

export function RegisterForm() {
  const router = useRouter();
  const registerMutation = useRegister();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "", display_name: "" },
  });

  const password = watch("password");
  const strength = getPasswordStrength(password);

  const onSubmit = async (data: RegisterFormData) => {
    setServerError(null);
    try {
      await registerMutation.mutateAsync(data);
      router.push("/login?registered=true");
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      const message =
        axiosError.response?.data?.detail ??
        "Error en el registro. Por favor, inténtalo de nuevo.";
      setServerError(message);
    }
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      sx={{ display: "flex", flexDirection: "column", gap: 2.5 }}
    >
      {serverError && (
        <Alert severity="error" onClose={() => setServerError(null)}>
          {serverError}
        </Alert>
      )}

      <TextField
        {...register("display_name")}
        label="Nombre"
        autoComplete="name"
        error={!!errors.display_name}
        helperText={errors.display_name?.message}
        fullWidth
      />

      <TextField
        {...register("email")}
        label="Correo electrónico"
        type="email"
        autoComplete="email"
        error={!!errors.email}
        helperText={errors.email?.message}
        fullWidth
      />

      <Box>
        <TextField
          {...register("password")}
          label="Contraseña"
          type="password"
          autoComplete="new-password"
          error={!!errors.password}
          helperText={errors.password?.message}
          fullWidth
        />
        {password.length > 0 && (
          <Box sx={{ mt: 1 }}>
            <LinearProgress
              variant="determinate"
              value={strength}
              color={strengthColor(strength)}
              sx={{ height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
              Seguridad de la contraseña: {strengthLabel(strength)}
            </Typography>
          </Box>
        )}
      </Box>

      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={isSubmitting}
        fullWidth
        sx={{ mt: 1 }}
      >
        {isSubmitting ? <CircularProgress size={24} /> : "Crear cuenta"}
      </Button>
    </Box>
  );
}
