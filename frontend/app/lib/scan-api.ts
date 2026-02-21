/**
 * Scan API - integration with Go Scan Service
 */

import { getDeviceFingerprint } from "./fingerprint";

const API_BASE = process.env.NEXT_PUBLIC_SCAN_API_URL || "http://localhost:8080";
const TIMEOUT_MS = 15000;

export interface ScanMetadata {
  latitude?: number;
  longitude?: number;
  fingerprint?: string;
}

export type ScanStatus = "original" | "warning" | "fake";

export interface ScanProduct {
  name: string;
  batch: string;
  factory: string;
  manufactured_at: string;
}

export interface ScanResponse {
  status: ScanStatus;
  product?: ScanProduct;
  scan_count?: number;
  first_scan_at?: string;
  risk_score?: number;
}

/** Extract code from QR/NFC payload - supports URL or raw UUID */
function extractCode(payload: string): string {
  const trimmed = payload.trim();
  try {
    const url = new URL(trimmed);
    const serial = url.searchParams.get("serial") ?? url.searchParams.get("tag_id") ?? url.pathname.split("/").pop();
    if (serial) return serial;
  } catch {
    // Not a URL, use as-is
  }
  return trimmed;
}

export async function scanProduct(
  code: string,
  metadata?: ScanMetadata
): Promise<ScanResponse> {
  const tagId = extractCode(code);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const fp = metadata?.fingerprint ?? (typeof window !== "undefined" ? getDeviceFingerprint() : "");
  if (fp) headers["X-Device-Fingerprint"] = fp;
  if (metadata?.latitude != null) headers["X-Latitude"] = String(metadata.latitude);
  if (metadata?.longitude != null) headers["X-Longitude"] = String(metadata.longitude);

  try {
    const res = await fetch(`${API_BASE}/v1/scan`, {
      method: "POST",
      headers,
      body: JSON.stringify({ code: tagId }),
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (!res.ok) {
      if (res.status === 404 || res.status === 400) {
        return { status: "fake", risk_score: 1 };
      }
      if (res.status === 429) {
        throw new Error("Muitas tentativas. Tente novamente em alguns instantes.");
      }
      throw new Error("Verificação temporariamente indisponível.");
    }

    const data = await res.json();

    const mapStatus = (valid: boolean, scanCount: number): ScanStatus => {
      if (!valid) return "fake";
      if (scanCount > 3) return "warning";
      return "original";
    };

    const status = data.status ?? mapStatus(data.valid ?? false, data.scan_count ?? 1);
    return {
      status,
      product: data.product
        ? {
            name: data.product.name ?? "Produto",
            batch: data.product.batch ?? data.batch_id ?? "-",
            factory: data.product.factory ?? "Voke Brasil",
            manufactured_at: data.product.manufactured_at ?? data.manufactured_at ?? "-",
          }
        : undefined,
      scan_count: data.scan_count ?? 1,
      first_scan_at: data.first_scan_at ?? data.timestamp,
      risk_score: data.risk_score ?? 0,
    };
  } catch (err) {
    clearTimeout(timeout);
    if (err instanceof Error) {
      if (err.name === "AbortError") throw new Error("Tempo esgotado. Verifique sua conexão.");
      throw err;
    }
    throw new Error("Erro ao verificar produto.");
  }
}

export type ReportType = "irregularity" | "fake";

export async function reportScan(
  code: string,
  reason: string,
  details: string,
  reportType: ReportType
): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code,
      reason,
      details,
      report_type: reportType,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { message?: string }).message || "Erro ao enviar reporte.");
  }
}

export async function scanProductWithRetry(
  code: string,
  metadata?: ScanMetadata
): Promise<ScanResponse> {
  try {
    return await scanProduct(code, metadata);
  } catch (e) {
    await new Promise((r) => setTimeout(r, 500));
    return scanProduct(code, metadata);
  }
}
