"use client";

import AuthGuard from "@/components/AuthGuard";

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>;
}
