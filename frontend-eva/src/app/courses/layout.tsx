"use client";

import AuthGuard from "@/components/AuthGuard";

export default function CoursesLayout({ children }: { children: React.ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>;
}
