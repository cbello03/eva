"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  TextField,
} from "@mui/material";
import { useLogin } from "@/features/auth/hooks";
import { loginSchema, type LoginFormData } from "@/features/auth/schemas";
import { useAuthStore } from "@/features/auth/store";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { AxiosError } from "axios";

export function LoginForm() {
  const router = useRouter();
  const loginMutation = useLogin();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);
    try {
      await loginMutation.mutateAsync(data);
      const role = useAuthStore.getState().user?.role;
      router.push(role === "teacher" || role === "admin" ? "/teacher" : "/dashboard");
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      const message =
        axiosError.response?.data?.detail ??
        "Credenciales inválidas. Por favor, inténtalo de nuevo.";
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
        {...register("email")}
        label="Correo electrónico"
        type="email"
        autoComplete="email"
        error={!!errors.email}
        helperText={errors.email?.message}
        fullWidth
      />

      <TextField
        {...register("password")}
        label="Contraseña"
        type="password"
        autoComplete="current-password"
        error={!!errors.password}
        helperText={errors.password?.message}
        fullWidth
      />

      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={isSubmitting}
        fullWidth
        sx={{ mt: 1 }}
      >
        {isSubmitting ? <CircularProgress size={24} /> : "Iniciar sesión"}
      </Button>
    </Box>
  );
}
