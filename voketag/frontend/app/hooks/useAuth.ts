"use client";

import { useState, useEffect } from "react";
import { isValidEmail } from "@/lib/sanitize";

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

/**
 * Authentication hook with secure token management.
 * 
 * HIGH SECURITY FIX: Tokens managed in-memory, not localStorage.
 * Uses httpOnly cookies set by the backend for token storage.
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // HIGH SECURITY FIX: Check authentication via API call, not localStorage
    // The token is stored in httpOnly cookie by backend
    const checkAuth = async () => {
      try {
        const response = await fetch("/api/auth/me", {
          credentials: "include",  // Include httpOnly cookies
        });
        
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          setUser(null);
        }
      } catch (e) {
        console.error("Failed to check auth status:", e);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    // HIGH SECURITY FIX: Validate input before sending
    
    // Validation 1: Email format
    if (!isValidEmail(email)) {
      throw new Error("Email inválido");
    }
    
    // Validation 2: Password requirements
    if (!password || password.length < 8) {
      throw new Error("Senha deve ter pelo menos 8 caracteres");
    }
    
    // Validation 3: Password max length (prevent DoS)
    if (password.length > 128) {
      throw new Error("Senha muito longa");
    }
    
    // HIGH SECURITY FIX: Proper error handling
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include",  // Include httpOnly cookies
      });
      
      if (!response.ok) {
        // Parse error message from response
        let errorMessage = "Login falhou";
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.detail || errorMessage;
        } catch {
          // Use default message if JSON parse fails
        }
        throw new Error(errorMessage);
      }
      
      // Parse user data from response
      const data = await response.json();
      
      // Validate response structure
      if (!data.user || !data.user.id || !data.user.email) {
        throw new Error("Resposta inválida do servidor");
      }
      
      // HIGH SECURITY FIX: Token is set by backend as httpOnly cookie
      // We only store user data in state (no token in localStorage)
      setUser({
        id: data.user.id,
        email: data.user.email,
        name: data.user.name || "",
        role: data.user.role || "user",
      });
      
    } catch (error) {
      // Re-throw with proper error message
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("Erro ao fazer login");
    }
  };

  const logout = async () => {
    try {
      // Call logout API to clear httpOnly cookie
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      console.error("Logout failed:", e);
    } finally {
      // Always clear user state
      setUser(null);
    }
  };

  return { user, loading, login, logout };
}
