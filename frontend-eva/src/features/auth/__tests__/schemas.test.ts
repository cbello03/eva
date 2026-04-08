import { describe, it, expect } from "vitest";
import { loginSchema, registerSchema } from "@/features/auth/schemas";

describe("loginSchema", () => {
  it("accepts valid email and password", () => {
    const result = loginSchema.safeParse({
      email: "user@example.com",
      password: "mypassword",
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid email format", () => {
    const result = loginSchema.safeParse({
      email: "not-an-email",
      password: "mypassword",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty email", () => {
    const result = loginSchema.safeParse({
      email: "",
      password: "mypassword",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty password", () => {
    const result = loginSchema.safeParse({
      email: "user@example.com",
      password: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing fields", () => {
    const result = loginSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});

describe("registerSchema", () => {
  const validData = {
    email: "student@example.com",
    display_name: "Test Student",
    password: "Secure1pass",
  };

  it("accepts valid registration data", () => {
    const result = registerSchema.safeParse(validData);
    expect(result.success).toBe(true);
  });

  // Email validation
  it("rejects invalid email", () => {
    const result = registerSchema.safeParse({ ...validData, email: "bad" });
    expect(result.success).toBe(false);
  });

  // Display name validation
  it("rejects display name shorter than 2 characters", () => {
    const result = registerSchema.safeParse({ ...validData, display_name: "A" });
    expect(result.success).toBe(false);
  });

  it("rejects display name longer than 100 characters", () => {
    const result = registerSchema.safeParse({
      ...validData,
      display_name: "A".repeat(101),
    });
    expect(result.success).toBe(false);
  });

  it("accepts display name at boundary (2 chars)", () => {
    const result = registerSchema.safeParse({ ...validData, display_name: "AB" });
    expect(result.success).toBe(true);
  });

  // Password validation
  it("rejects password shorter than 8 characters", () => {
    const result = registerSchema.safeParse({ ...validData, password: "Ab1" });
    expect(result.success).toBe(false);
  });

  it("rejects password without uppercase letter", () => {
    const result = registerSchema.safeParse({ ...validData, password: "lowercase1" });
    expect(result.success).toBe(false);
  });

  it("rejects password without lowercase letter", () => {
    const result = registerSchema.safeParse({ ...validData, password: "UPPERCASE1" });
    expect(result.success).toBe(false);
  });

  it("rejects password without a number", () => {
    const result = registerSchema.safeParse({ ...validData, password: "NoDigitsHere" });
    expect(result.success).toBe(false);
  });

  it("accepts password that meets all criteria", () => {
    const result = registerSchema.safeParse({ ...validData, password: "GoodPass1" });
    expect(result.success).toBe(true);
  });
});
