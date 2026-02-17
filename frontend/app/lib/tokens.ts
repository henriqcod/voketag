/**
 * Secure Token Management
 * 
 * Strategy:
 * - Access token: In-memory only (never localStorage)
 * - Refresh token: HttpOnly cookie
 * - Silent refresh mechanism
 * - Auto logout on refresh failure
 */

let accessToken: string | null = null;
let refreshTimer: NodeJS.Timeout | null = null;

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number; // seconds
}

/**
 * Set access token in memory
 */
export function setAccessToken(token: string): void {
  accessToken = token;
}

/**
 * Get access token from memory
 */
export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * Clear access token from memory
 */
export function clearAccessToken(): void {
  accessToken = null;
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
}

/**
 * Initialize tokens after login
 * Sets up silent refresh mechanism
 */
export function initializeTokens(tokens: TokenPair): void {
  setAccessToken(tokens.accessToken);
  
  // Schedule silent refresh before expiration
  // Refresh at 80% of token lifetime (e.g., 12min for 15min token)
  const refreshIn = tokens.expiresIn * 0.8 * 1000; // Convert to ms
  
  refreshTimer = setTimeout(() => {
    silentRefresh().catch((error) => {
      console.error("Silent refresh failed:", error);
      handleRefreshFailure();
    });
  }, refreshIn);
}

/**
 * Silent refresh using refresh token (HttpOnly cookie)
 */
async function silentRefresh(): Promise<void> {
  try {
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include", // Include HttpOnly cookie
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Refresh failed: ${response.status}`);
    }

    const data: TokenPair = await response.json();
    
    // Update access token and schedule next refresh
    initializeTokens(data);
  } catch (error) {
    throw error;
  }
}

/**
 * Handle refresh failure - logout user
 */
function handleRefreshFailure(): void {
  clearAccessToken();
  
  // Redirect to login
  if (typeof window !== "undefined") {
    window.location.href = "/login?session_expired=true";
  }
}

/**
 * Logout - clear tokens and notify backend
 */
export async function logout(): Promise<void> {
  try {
    // Notify backend to invalidate refresh token
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  } catch (error) {
    console.error("Logout API call failed:", error);
  } finally {
    clearAccessToken();
    
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return accessToken !== null;
}

/**
 * Get authorization header for API requests
 */
export function getAuthHeader(): { Authorization: string } | {} {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
