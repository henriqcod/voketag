/**
 * Logs & Audit API.
 * Backend has audit logging; API for retrieval may be added.
 */

export interface AuditLog {
  id: string;
  action: string;
  actor: string;
  ip: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface LogsResponse {
  items: AuditLog[];
  total: number;
}

export interface LogsFilters {
  skip?: number;
  limit?: number;
  action?: string;
  actor?: string;
  date_from?: string;
  date_to?: string;
}

const MOCK_LOGS: AuditLog[] = [
  { id: "1", action: "upload_csv", actor: "admin@voketag.com", ip: "192.168.1.1", timestamp: new Date().toISOString(), details: { batch_id: "b1", rows: 150 } },
  { id: "2", action: "batch_anchored", actor: "admin@voketag.com", ip: "192.168.1.1", timestamp: new Date(Date.now() - 3600000).toISOString(), details: { batch_id: "b1", merkle_root: "0x1234..." } },
  { id: "3", action: "login_failed", actor: "unknown", ip: "10.0.0.1", timestamp: new Date(Date.now() - 7200000).toISOString() },
];

export async function fetchLogs(params?: LogsFilters): Promise<LogsResponse> {
  const q = new URLSearchParams();
  if (params?.skip != null) q.set("skip", String(params.skip));
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.action) q.set("action", params.action);
  if (params?.actor) q.set("actor", params.actor);
  if (params?.date_from) q.set("date_from", params.date_from);
  if (params?.date_to) q.set("date_to", params.date_to);
  const query = q.toString();
  try {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/v1";
    const token = typeof window !== "undefined" ? localStorage.getItem("voketag_token") : null;
    const res = await fetch(`${API_BASE}/audit/logs${query ? `?${query}` : ""}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (res.ok) return res.json();
    throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    if (isNetworkOr5xx(err)) return { items: MOCK_LOGS, total: MOCK_LOGS.length };
    throw err;
  }
}

function isNetworkOr5xx(err: unknown): boolean {
  if (err instanceof Error && err.message.startsWith("HTTP 5")) return true;
  if (err instanceof TypeError && err.message.includes("fetch")) return true;
  return false;
}
