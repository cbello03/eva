import { z } from "zod";

// ── Login Schema ─────────────────────────────────────────────────────

export const loginSchema = z.object({
  email: z.email("Por favor, ingresa un correo electrónico válido"),
  password: z.string().min(1, "La contraseña es obligatoria"),
});

export type LoginFormData = z.infer<typeof loginSchema>;

// ── Register Schema ──────────────────────────────────────────────────

export const registerSchema = z.object({
  email: z.email("Por favor, ingresa un correo electrónico válido"),
  display_name: z
    .string()
    .min(2, "El nombre debe tener al menos 2 caracteres")
    .max(100, "El nombre debe tener como máximo 100 caracteres"),
  password: z
    .string()
    .min(8, "La contraseña debe tener al menos 8 caracteres")
    .regex(/[A-Z]/, "La contraseña debe contener al menos una letra mayúscula")
    .regex(/[a-z]/, "La contraseña debe contener al menos una letra minúscula")
    .regex(/[0-9]/, "La contraseña debe contener al menos un número"),
});

export type RegisterFormData = z.infer<typeof registerSchema>;
