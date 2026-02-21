/**
 * Settings API - factory configuration.
 */

export interface FactorySettings {
  verification_url: string;
  ntag_default: "213" | "215" | "216";
  webhook_url?: string;
  antifraud_scan_threshold: number;
  sandbox_mode: boolean;
}

const DEFAULT: FactorySettings = {
  verification_url: "https://verify.voketag.com.br",
  ntag_default: "216",
  antifraud_scan_threshold: 5,
  sandbox_mode: false,
};

export async function fetchSettings(): Promise<FactorySettings> {
  try {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/v1";
    const token = typeof window !== "undefined" ? localStorage.getItem("voketag_token") : null;
    const res = await fetch(`${API_BASE}/settings`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (res.ok) return res.json();
  } catch {}
  const stored = typeof window !== "undefined" ? localStorage.getItem("voketag_settings") : null;
  if (stored) {
    try {
      return { ...DEFAULT, ...JSON.parse(stored) };
    } catch {}
  }
  return DEFAULT;
}

export async function saveSettings(data: Partial<FactorySettings>): Promise<FactorySettings> {
  const current = await fetchSettings();
  const next = { ...current, ...data };
  try {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/v1";
    const token = typeof window !== "undefined" ? localStorage.getItem("voketag_token") : null;
    const res = await fetch(`${API_BASE}/settings`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(next),
    });
    if (res.ok) return res.json();
  } catch {}
  if (typeof window !== "undefined") {
    localStorage.setItem("voketag_settings", JSON.stringify(next));
  }
  return next;
}
