import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Route guard middleware.
 *
 * Since the Access_Token lives only in memory (Zustand), we can't read it
 * server-side. Instead we check for the presence of the httpOnly refresh
 * cookie as a proxy for "user has an active session". The actual auth
 * validation still happens on the API layer — this middleware only provides
 * a fast redirect UX so unauthenticated users don't see a flash of
 * protected content.
 */

// Routes that require authentication
const PROTECTED_PREFIXES = [
  "/dashboard",
  "/courses",
  "/projects",
  "/profile",
  "/teacher",
];

// Routes only accessible to unauthenticated users
const GUEST_ONLY = ["/login", "/register"];

// Routes restricted to teacher/admin roles (cookie can't tell us the role,
// so we only enforce the "logged-in" check here; role enforcement happens
// on the API side and via client-side guards in the page components).
const TEACHER_PREFIXES = ["/teacher"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check for refresh token cookie as session indicator
  const hasSession = request.cookies.has("refresh_token");

  // Redirect unauthenticated users away from protected routes
  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(prefix + "/"),
  );

  if (isProtected && !hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect authenticated users away from guest-only routes
  const isGuestOnly = GUEST_ONLY.some(
    (route) => pathname === route || pathname.startsWith(route + "/"),
  );

  if (isGuestOnly && hasSession) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/courses/:path*",
    "/projects/:path*",
    "/profile/:path*",
    "/teacher/:path*",
    "/login",
    "/register",
  ],
};
