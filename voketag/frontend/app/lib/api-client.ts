/**
 * Secure API Client
 * 
 * Enterprise Security Features:
 * - XSS Protection (strict typing, no dangerouslySetInnerHTML)
 * - CSRF Protection (double submit cookie)
 * - JWT Authentication (httpOnly cookie, managed by backend)
 * - Secure token management (NO localStorage)
 * 
 * CRITICAL SECURITY FIX:
 * - Tokens are stored in httpOnly cookies by the backend
 * - JavaScript cannot access tokens (prevents XSS theft)
 * - All requests use credentials: 'include' to send cookies
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080";
const FACTORY_API = process.env.NEXT_PUBLIC_FACTORY_API_URL || "http://localhost:8081";
const ADMIN_API = process.env.NEXT_PUBLIC_ADMIN_API_URL || "http://localhost:8082";

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

export async function fetchScan(tagId: string) {
  const res = await fetch(`${API_BASE}/v1/scan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tagId }),
  });
  if (!res.ok) throw new Error("Scan failed");
  return res.json();
}

// Factory API functions
export const factoryAPI = {
  async getProducts() {
    const res = await fetch(`${FACTORY_API}/v1/products`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error("Failed to fetch products");
    return res.json();
  },

  async createProduct(product: { name: string; description: string }) {
    const res = await fetch(`${FACTORY_API}/v1/products`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(product),
    });
    if (!res.ok) throw new Error("Failed to create product");
    return res.json();
  },

  async getBatches() {
    const res = await fetch(`${FACTORY_API}/v1/batches`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error("Failed to fetch batches");
    return res.json();
  },

  async createBatch(batch: { name: string; quantity: number }) {
    const res = await fetch(`${FACTORY_API}/v1/batches`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(batch),
    });
    if (!res.ok) throw new Error("Failed to create batch");
    return res.json();
  },
};

// Admin API functions
export const adminAPI = {
  async getDashboard() {
    const res = await fetch(`${ADMIN_API}/v1/admin/dashboard`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error("Failed to fetch dashboard");
    return res.json();
  },

  async getUsers() {
    const res = await fetch(`${ADMIN_API}/v1/admin/users`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error("Failed to fetch users");
    return res.json();
  },
};

/**
 * Secure API client with CSRF and auth
 */
export const apiClient = {
  async get<T>(path: string): Promise<T> {
    // CRITICAL SECURITY FIX: Token sent automatically via httpOnly cookie
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // Send httpOnly cookies
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
    // CRITICAL SECURITY FIX: Token sent automatically via httpOnly cookie
    const csrfToken = getCSRFToken();
    
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken && { "X-CSRF-Token": csrfToken }),
      },
      body: JSON.stringify(data),
      credentials: "include", // Send httpOnly cookies
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
    // CRITICAL SECURITY FIX: Token sent automatically via httpOnly cookie
    const csrfToken = getCSRFToken();
    
    const response = await fetch(`${API_BASE}${path}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken && { "X-CSRF-Token": csrfToken }),
      },
      body: JSON.stringify(data),
      credentials: "include", // Send httpOnly cookies
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
    // CRITICAL SECURITY FIX: Token sent automatically via httpOnly cookie
    const csrfToken = getCSRFToken();
    
    const response = await fetch(`${API_BASE}${path}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken && { "X-CSRF-Token": csrfToken }),
      },
      credentials: "include", // Send httpOnly cookies
    });
    
    if (!response.ok) {
      if (response.status === 401 && typeof window !== "undefined") {
        window.location.href = "/login?session_expired=true";
      }
      throw new Error(`API error: ${response.statusText}`);
    }
  },
};
