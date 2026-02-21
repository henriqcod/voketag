import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { hasAuthCookie, getRoleFromCookies } from "@/lib/auth-cookies";

const PUBLIC = ["/", "/login"];
const ADMIN_ONLY = ["/audit", "/settings"];

function isPublic(path: string) {
  return PUBLIC.includes(path) || path.startsWith("/login");
}

function isAdminOnly(path: string) {
  return ADMIN_ONLY.some((p) => path === p || path.startsWith(p + "/"));
}

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const cookieHeader = request.headers.get("cookie");

  if (path === "/") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (isPublic(path)) {
    if (path === "/login" && hasAuthCookie(cookieHeader)) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    return NextResponse.next();
  }

  if (!hasAuthCookie(cookieHeader)) {
    const login = new URL("/login", request.url);
    login.searchParams.set("redirect", path);
    return NextResponse.redirect(login);
  }

  if (isAdminOnly(path) && getRoleFromCookies(cookieHeader) !== "admin") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|favicon.ico|api).*)"],
};
