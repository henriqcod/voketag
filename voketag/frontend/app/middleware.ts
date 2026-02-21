import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Security Headers - Enterprise Hardening
  response.headers.set("X-DNS-Prefetch-Control", "on");
  response.headers.set("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload");
  response.headers.set("X-Frame-Options", "SAMEORIGIN");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set("X-XSS-Protection", "1; mode=block");
  
  // HIGH SECURITY FIX: Strict CSP without unsafe-eval and unsafe-inline
  // Generate nonce for inline scripts (if needed)
  const nonce = generateNonce();
  
  // Content Security Policy - STRICT MODE
  const apiDomain = process.env.NEXT_PUBLIC_API_URL || "https://api.voketag.com.br";
  const csp = [
    "default-src 'self'",
    // HIGH FIX: Removed 'unsafe-eval' and 'unsafe-inline'
    // Use nonce for inline scripts if absolutely necessary
    `script-src 'self' 'nonce-${nonce}'`,
    // Allow inline styles with hash or nonce for Next.js
    `style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    `connect-src 'self' ${apiDomain}`,
    "frame-ancestors 'self'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",  // Block Flash, Java applets
    "upgrade-insecure-requests",  // Force HTTPS
  ].join("; ");
  
  response.headers.set("Content-Security-Policy", csp);
  // Store nonce for use in pages if needed
  response.headers.set("X-Nonce", nonce);

  // Permissions Policy
  response.headers.set(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=(), interest-cohort=()"
  );

  // Protected routes - check auth
  const token = request.cookies.get("auth_token");
  const protectedPaths = ["/dashboard", "/products", "/batches", "/api-keys"];
  
  const isProtected = protectedPaths.some((path) =>
    request.nextUrl.pathname.startsWith(path)
  );

  if (isProtected && !token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // CSRF Token - set cookie for state-changing requests
  if (!request.cookies.get("csrf_token")) {
    const csrfToken = generateCSRFToken();
    response.cookies.set("csrf_token", csrfToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
    });
  }

  return response;
}

function generateNonce(): string {
  // Generate cryptographically secure nonce for CSP
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID().replace(/-/g, "");
  }
  // Fallback: use timestamp + random
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

function generateCSRFToken(): string {
  // Generate secure random token
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older environments
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|public).*)",
  ],
};
