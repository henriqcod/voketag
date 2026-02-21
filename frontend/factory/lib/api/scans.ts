export interface ScanEvent {
  id: string;
  serial_number: string;
  batch_id: string;
  scanned_at: string;
  country?: string;
  device?: string;
  risk_status: "low" | "medium" | "high";
  is_duplicate: boolean;
}

export interface ScansResponse {
  items: ScanEvent[];
  total: number;
  activity_by_minute?: { minute: number; count: number }[];
}

export interface ScansFilters {
  batch_id?: string;
  country?: string;
  risk_status?: "low" | "medium" | "high";
  date_from?: string;
  date_to?: string;
  limit?: number;
  skip?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/v1";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("voketag_token")
      : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers as Record<string, string>) },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  if (res.status === 204) return undefined as T;
  return res.json();
}

const MOCK_SCANS: ScanEvent[] = [
  {
    id: "1",
    serial_number: "SN-2024-001234",
    batch_id: "b1",
    scanned_at: new Date().toISOString(),
    country: "BR",
    device: "Android",
    risk_status: "low",
    is_duplicate: false,
  },
  {
    id: "2",
    serial_number: "SN-2024-001235",
    batch_id: "b1",
    scanned_at: new Date(Date.now() - 120000).toISOString(),
    country: "PT",
    device: "iOS",
    risk_status: "low",
    is_duplicate: false,
  },
  {
    id: "3",
    serial_number: "SN-2024-001234",
    batch_id: "b1",
    scanned_at: new Date(Date.now() - 60000).toISOString(),
    country: "AR",
    device: "Android",
    risk_status: "high",
    is_duplicate: true,
  },
];

export async function fetchScans(params?: ScansFilters): Promise<ScansResponse> {
  const q = new URLSearchParams();
  if (params?.batch_id) q.set("batch_id", params.batch_id);
  if (params?.country) q.set("country", params.country);
  if (params?.risk_status) q.set("risk_status", params.risk_status);
  if (params?.date_from) q.set("date_from", params.date_from);
  if (params?.date_to) q.set("date_to", params.date_to);
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.skip != null) q.set("skip", String(params.skip));
  const query = q.toString();

  try {
    return await apiFetch<ScansResponse>(`/scans${query ? `?${query}` : ""}`);
  } catch (err) {
    if (isNetworkOr5xx(err)) {
      const now = new Date();
      return {
        items: MOCK_SCANS,
        total: MOCK_SCANS.length,
        activity_by_minute: Array.from({ length: 60 }, (_, i) => ({
          minute: (now.getMinutes() - 59 + i + 60) % 60,
          count: Math.floor(Math.random() * 20) + 2,
        })),
      };
    }
    throw err;
  }
}

function isNetworkOr5xx(err: unknown): boolean {
  if (err instanceof Error && err.message.startsWith("HTTP 5")) return true;
  if (err instanceof TypeError && err.message.includes("fetch")) return true;
  return false;
}

export async function fetchScanDetail(id: string): Promise<ScanEvent> {
  return apiFetch<ScanEvent>(`/scans/${id}`);
}
