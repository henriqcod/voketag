"use client";

/**
 * Antifraud API Client
 * Secure communication with verification endpoints
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080";

export interface VerificationResponse {
  valid: boolean;
  status: "authentic" | "warning" | "high_risk";
  risk_score: number;
  product?: {
    id: string;
    name: string;
    batch_id: string;
    manufactured_at?: string;
  };
  verification_id: string;
  timestamp: string;
  message: string;
  risk_factors?: Record<string, number>;
  metadata?: {
    total_scans?: number;
    unique_countries?: number;
    country?: string;
  };
}

export interface DeviceFingerprint {
  screen_resolution: string;
  timezone: string;
  language: string;
}

/**
 * Collect device fingerprint for antifraud
 */
export function collectFingerprint(): DeviceFingerprint {
  return {
    screen_resolution: `${window.screen.width}x${window.screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
  };
}

/**
 * Verify product using signed token
 */
export async function verifyProduct(token: string): Promise<VerificationResponse> {
  const fingerprint = collectFingerprint();
  
  const response = await fetch(`${API_BASE}/api/verify/${encodeURIComponent(token)}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Screen-Resolution": fingerprint.screen_resolution,
      "X-Timezone": fingerprint.timezone,
      "Accept-Language": fingerprint.language,
    },
    credentials: "omit", // No cookies needed for public verification
  });

  if (!response.ok) {
    if (response.status === 400) {
      throw new Error("Invalid verification token");
    }
    if (response.status === 410) {
      throw new Error("Verification token expired");
    }
    if (response.status === 429) {
      throw new Error("Too many verification attempts. Please try again later.");
    }
    throw new Error("Verification failed. Please try again.");
  }

  return response.json();
}

/**
 * Report fraudulent product
 */
export async function reportFraud(
  verificationId: string,
  reason: string,
  details?: string
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/fraud/report`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      verification_id: verificationId,
      reason,
      details,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to submit fraud report");
  }
}
