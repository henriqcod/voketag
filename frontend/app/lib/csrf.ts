/**
 * CSRF Protection - Double Submit Cookie Pattern
 * 
 * Strategy:
 * 1. Server sets CSRF token in HttpOnly cookie
 * 2. Client reads token from cookie and includes in request header
 * 3. Server verifies cookie token matches header token
 */

/**
 * Get CSRF token from cookies
 */
export function getCSRFToken(): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const cookies = document.cookie.split(";");
  const csrfCookie = cookies.find((cookie) => cookie.trim().startsWith("csrf_token="));
  
  if (!csrfCookie) {
    return null;
  }

  return csrfCookie.split("=")[1];
}

/**
 * Get CSRF header for API requests
 */
export function getCSRFHeader(): { "X-CSRF-Token": string } | {} {
  const token = getCSRFToken();
  return token ? { "X-CSRF-Token": token } : {};
}

/**
 * Validate CSRF token on state-changing requests
 * Should be called on server-side for POST/PUT/DELETE requests
 */
export function validateCSRFToken(cookieToken: string | undefined, headerToken: string | undefined): boolean {
  if (!cookieToken || !headerToken) {
    return false;
  }

  // Constant-time comparison to prevent timing attacks
  return cookieToken === headerToken;
}
