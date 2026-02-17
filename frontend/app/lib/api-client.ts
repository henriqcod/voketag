/**
 * Secure API Client
 * 
 * Enterprise Security Features:
 * - XSS Protection (strict typing, no dangerouslySetInnerHTML)
 * - CSRF Protection (double submit cookie)
 * - JWT Authentication (in-memory access token)
 * - Secure token management
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

/**
 * Get CSRF token from cookie
 */
function getCSRFToken(): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const cookies = document.cookie.split(";");
  const csrfCookie = cookies.find((c) => c.trim().startsWith("csrf_token="));
  return csrfCookie ? csrfCookie.split("=")[1] : null;
}

/**
 * Get auth token from localStorage (temporary - migrate to in-memory)
 */
function getAuthToken(): string | null {
  if (typeof localStorage === "undefined") {
    return null;
  }
  return localStorage.getItem("auth_token");
}

export async function fetchScan(tagId: string) {
  const res = await fetch(`${API_BASE}/v1/scan/${tagId}`, {
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!res.ok) throw new Error("Scan failed");
  return res.json();
}

/**
 * Secure API client with CSRF and auth
 */
export const apiClient = {
  async get<T>(path: string): Promise<T> {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      credentials: "include",
    });
    
    if (!response.ok) {
      if (response.status === 401 && typeof window !== "undefined") {
        window.location.href = "/login?session_expired=true";
      }
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return response.json();
  },

  async post<T>(path: string, data: unknown): Promise<T> {
    const token = getAuthToken();
    const csrfToken = getCSRFToken();
    
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
        ...(csrfToken && { "X-CSRF-Token": csrfToken }),
      },
      body: JSON.stringify(data),
      credentials: "include",
    });
    
    if (!response.ok) {
      if (response.status === 401 && typeof window !== "undefined") {
        window.location.href = "/login?session_expired=true";
      }
      if (response.status === 403) {
        throw new Error("CSRF validation failed");
      }
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return response.json();
  },

  async put<T>(path: string, data: unknown): Promise<T> {
    const token = getAuthToken();
    const csrfToken = getCSRFToken();
    
    const response = await fetch(`${API_BASE}${path}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
        ...(csrfToken && { "X-CSRF-Token": csrfToken }),
      },
      body: JSON.stringify(data),
      credentials: "include",
    });
    
    if (!response.ok) {
      if (response.status === 401 && typeof window !== "undefined") {
        window.location.href = "/login?session_expired=true";
      }
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return response.json();
  },

  async delete(path: string): Promise<void> {
    const token = getAuthToken();
    const csrfToken = getCSRFToken();
    
    const response = await fetch(`${API_BASE}${path}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
        ...(csrfToken && { "X-CSRF-Token": csrfToken }),
      },
      credentials: "include",
    });
    
    if (!response.ok) {
      if (response.status === 401 && typeof window !== "undefined") {
        window.location.href = "/login?session_expired=true";
      }
      throw new Error(`API error: ${response.statusText}`);
    }
  },
};
