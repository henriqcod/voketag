import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TOKEN_COOKIE = "admin_token";

function isPublicPath(pathname: string): boolean {
  return (
    pathname === "/login" ||
    pathname.startsWith("/_next") ||
    pathname === "/favicon.ico" ||
    pathname.startsWith("/api/admin/v1/admin/auth/login") ||
    pathname.startsWith("/api/admin/v1/admin/auth/refresh")
  );
}

function isProtectedPath(pathname: string): boolean {
  if (pathname.startsWith("/api")) return false;
  const protectedPrefixes = ["/dashboard", "/users", "/factory", "/scans", "/antifraud", "/audit", "/monitoring", "/settings"];
  return pathname === "/" || protectedPrefixes.some((p) => pathname.startsWith(p));
}

/**
 * Decode JWT payload without verifying signature (Edge-safe).
 * Returns payload or null if invalid/malformed.
 */
function decodeJwtPayload(token: string): { exp?: number } | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payloadB64 = parts[1];
    const base64 = payloadB64.replace(/-/g, "+").replace(/_/g, "/");
    const padding = base64.length % 4;
    const padded = padding ? base64 + "=".repeat(4 - padding) : base64;
    const decoded = atob(padded);
    return JSON.parse(decoded) as { exp?: number };
  } catch {
    return null;
  }
}

/**
 * Check if JWT is valid: exists, decodable, and not expired.
 * Uses 60s grace period to avoid edge-case redirects during refresh.
 */
function isJwtValid(token: string | undefined): boolean {
  if (!token || typeof token !== "string") return false;
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== "number") return false;
  const nowSeconds = Math.floor(Date.now() / 1000);
  const graceSeconds = 60;
  return payload.exp > nowSeconds - graceSeconds;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (isPublicPath(pathname)) return NextResponse.next();

  if (!isProtectedPath(pathname)) return NextResponse.next();

  const token = request.cookies.get(TOKEN_COOKIE)?.value;
  if (!isJwtValid(token)) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("expired", "1");
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
