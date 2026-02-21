/**
 * Auth cookie helpers - used for middleware (server) and login (client).
 * Cookie is read by middleware; localStorage keeps token for API calls.
 */

export type Role = "admin" | "operador";

const TOKEN_KEY = "voketag_token";
const ROLE_KEY = "voketag_role";
const COOKIE_TOKEN = "voketag_token";
const COOKIE_ROLE = "voketag_role";
const MAX_AGE = 60 * 60 * 24; // 24h

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function getRoleFromJwt(token: string): Role {
  const payload = decodeJwtPayload(token);
  if (!payload) return "operador";
  const roles = payload.roles as string[] | undefined;
  const role = (payload.role ?? (Array.isArray(roles) ? roles[0] : undefined)) as string | undefined;
  if (role === "admin" || role === "administrator") return "admin";
  return "operador";
}

/** Client-only: set auth after login */
export function setAuthCookies(token: string, role?: Role): void {
  if (typeof window === "undefined") return;
  const r = role ?? getRoleFromJwt(token);
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, r);
  document.cookie = `${COOKIE_TOKEN}=${encodeURIComponent(token)}; path=/; max-age=${MAX_AGE}; SameSite=Lax`;
  document.cookie = `${COOKIE_ROLE}=${r}; path=/; max-age=${MAX_AGE}; SameSite=Lax`;
}

/** Client-only: clear auth on logout */
export function clearAuthCookies(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  document.cookie = `${COOKIE_TOKEN}=; path=/; max-age=0`;
  document.cookie = `${COOKIE_ROLE}=; path=/; max-age=0`;
}

/** Server (middleware): get role from request cookies */
export function getRoleFromCookies(cookieHeader: string | null): Role {
  if (!cookieHeader) return "operador";
  const cookies = Object.fromEntries(
    cookieHeader.split(";").map((c) => {
      const [k, v] = c.trim().split("=");
      return [k, v ? decodeURIComponent(v) : ""];
    })
  );
  const role = cookies[COOKIE_ROLE];
  return role === "admin" ? "admin" : "operador";
}

/** Server (middleware): check if token exists */
export function hasAuthCookie(cookieHeader: string | null): boolean {
  if (!cookieHeader) return false;
  const cookies = Object.fromEntries(
    cookieHeader.split(";").map((c) => {
      const [k, v] = c.trim().split("=");
      return [k, v ?? ""];
    })
  );
  return !!cookies[COOKIE_TOKEN];
}
