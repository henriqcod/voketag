// Use proxy (same-origin) to avoid CORS; fallback to direct API URL
const BASE_URL =
  typeof window !== "undefined"
    ? "/api/admin"
    : (process.env.NEXT_PUBLIC_ADMIN_API || "http://127.0.0.1:8082");

const TOKEN_KEY = "admin_token";
const REFRESH_KEY = "admin_refresh_token";
const TOKEN_COOKIE = "admin_token";
const CSRF_HEADER = "X-CSRF-Token";

let csrfTokenCache: string | null = null;

function isMutation(method?: string): boolean {
  return ["POST", "PUT", "PATCH", "DELETE"].includes(method ?? "GET");
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

function setTokenCookie(token: string, maxAgeSeconds = 3600): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(token)}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax`;
}

function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0`;
  clearCsrfCache();
  window.location.href = "/login";
}

async function ensureCsrfToken(): Promise<string> {
  if (csrfTokenCache) return csrfTokenCache;
  csrfTokenCache = await getCsrfToken();
  return csrfTokenCache;
}

function clearCsrfCache(): void {
  csrfTokenCache = null;
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const csrf = await ensureCsrfToken();
    const res = await fetch(`${BASE_URL}/v1/admin/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json", [CSRF_HEADER]: csrf },
      body: JSON.stringify({ refresh_token: refresh }),
      credentials: "include",
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { access_token: string; expires_in?: number };
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setTokenCookie(data.access_token, data.expires_in ?? 3600);
    return data.access_token;
  } catch {
    return null;
  }
}

async function fetchWithAuth<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  let token = getToken();
  if (!token) {
    token = await refreshAccessToken();
  }
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(init?.headers || {}),
  };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  const method = (init?.method ?? "GET").toUpperCase();
  if (isMutation(method)) {
    const csrf = await ensureCsrfToken();
    (headers as Record<string, string>)[CSRF_HEADER] = csrf;
  }
  let res = await fetch(`${BASE_URL}${path}`, { ...init, headers, credentials: "include" });
  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${newToken}`;
      if (isMutation(method)) {
        (headers as Record<string, string>)[CSRF_HEADER] = await ensureCsrfToken();
      }
      res = await fetch(`${BASE_URL}${path}`, { ...init, headers, credentials: "include" });
    }
    if (res.status === 401) {
      clearToken();
      throw new Error("Unauthorized");
    }
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof err.detail === "string"
        ? err.detail
        : JSON.stringify(err.detail || err)
    );
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

// Auth (plain fetch - no token yet, 401 = bad credentials, don't clear/redirect)
export async function login(email: string, password: string) {
  let csrf: string;
  try {
    csrf = await getCsrfToken();
  } catch {
    throw new Error(
      "Não foi possível conectar ao Admin API. Verifique se o admin-service está rodando (porta 8082)."
    );
  }
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/v1/admin/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", [CSRF_HEADER]: csrf },
      body: JSON.stringify({ email, password }),
      credentials: "include",
    });
  } catch {
    throw new Error(
      "Erro de conexão com o Admin API. Verifique se o admin-service está rodando."
    );
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    const msg = typeof err.detail === "string" ? err.detail : "Login failed";
    if (res.status === 401) {
      throw new Error("Email ou senha inválidos. Verifique as credenciais.");
    }
    throw new Error(msg);
  }
  return res.json() as Promise<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    user_id: string;
    email: string;
    role: string;
    expires_in?: number;
  }>;
}

export async function getCsrfToken(): Promise<string> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}/v1/admin/auth/csrf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to get CSRF token");
  const data = (await res.json()) as { csrf_token: string };
  return data.csrf_token;
}

// Dashboard
export async function getDashboard(days = 30) {
  return fetchWithAuth<Record<string, unknown>>(
    `/v1/admin/dashboard?days=${days}`
  );
}

export async function getSystemStatus() {
  return fetchWithAuth<{ services: { service: string; url?: string; status: string; latency_ms?: number }[] }>(
    "/v1/admin/system/status"
  );
}

export interface SystemStatusExtended {
  uptime_seconds: number;
  redis_status: string;
  postgres_status: string;
  metrics_24h: Record<string, unknown>;
  services: { service: string; url: string; status: string; latency_ms?: number }[];
  api_latency_avg_ms: number | null;
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
}

export async function getSystemStatusExtended() {
  return fetchWithAuth<SystemStatusExtended>("/v1/admin/system/status/extended");
}

export async function getSystemConfig() {
  return fetchWithAuth<Record<string, unknown> & { prometheus_url?: string; grafana_url?: string }>(
    "/v1/admin/system/config"
  );
}

export async function getPrometheusMetrics(): Promise<string> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}/v1/admin/system/metrics`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.text();
}

// Users
export async function listUsers(params?: {
  skip?: number;
  limit?: number;
  role?: string;
  search?: string;
}) {
  const sp = new URLSearchParams();
  if (params?.skip != null) sp.set("skip", String(params.skip));
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.role) sp.set("role", params.role);
  if (params?.search) sp.set("search", params.search);
  const q = sp.toString();
  return fetchWithAuth<{ id: string; email: string; name: string; role: string; is_active: boolean; created_at: string; updated_at: string }[]>(
    `/v1/admin/users${q ? `?${q}` : ""}`
  );
}

export async function deleteUser(userId: string) {
  return fetchWithAuth<void>(`/v1/admin/users/${userId}`, { method: "DELETE" });
}

export async function updateUser(userId: string, data: { name?: string; email?: string; role?: string; is_active?: boolean }) {
  return fetchWithAuth<{ id: string; email: string; name: string; role: string }>(`/v1/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function blockUser(userId: string) {
  return fetchWithAuth<{ message: string }>(`/v1/admin/users/${userId}/block`, { method: "POST" });
}

export async function unblockUser(userId: string) {
  return fetchWithAuth<{ message: string }>(`/v1/admin/users/${userId}/unblock`, { method: "POST" });
}

export async function adminResetPassword(userId: string, newPassword: string) {
  return fetchWithAuth<{ message: string }>(`/v1/admin/users/${userId}/admin-reset-password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  });
}

export async function forceLogoutUser(userId: string) {
  return fetchWithAuth<{ message: string }>(`/v1/admin/users/${userId}/force-logout`, { method: "POST" });
}

export async function getLoginHistory(userId: string, limit = 50) {
  return fetchWithAuth<{ id: string; ip_address: string | null; user_agent: string; created_at: string }[]>(
    `/v1/admin/users/${userId}/login-history?limit=${limit}`
  );
}

export async function createUser(data: { name: string; email: string; password: string; role: string }) {
  return fetchWithAuth<{ id: string; email: string; name: string; role: string; is_active: boolean; created_at: string; updated_at: string }>(`/v1/admin/users`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Factory / Batches
export interface Batch {
  id: string;
  factory_id: string;
  product_count: number;
  status: string;
  merkle_root: string | null;
  blockchain_tx: string | null;
  created_at: string | null;
  anchored_at: string | null;
  error: string | null;
}

export async function listBatches(params?: { skip?: number; limit?: number; status?: string }) {
  const sp = new URLSearchParams();
  if (params?.skip != null) sp.set("skip", String(params.skip));
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.status) sp.set("status", params.status);
  const q = sp.toString();
  return fetchWithAuth<{ batches: Batch[]; total: number }>(`/v1/admin/factory/batches${q ? `?${q}` : ""}`);
}

export async function getBatchDetail(batchId: string) {
  return fetchWithAuth<Batch & { blockchain_task_id?: string; updated_at?: string; metadata?: unknown }>(
    `/v1/admin/factory/batches/${batchId}`
  );
}

export interface MerkleNode {
  hash: string;
  left?: MerkleNode | null;
  right?: MerkleNode | null;
  product_id?: string;
}

export interface MerkleTreeResponse {
  merkle_root: string | null;
  leaves: { product_id: string; hash: string }[];
  tree: MerkleNode | null;
  message?: string;
}

export async function getBatchMerkleTree(batchId: string) {
  return fetchWithAuth<MerkleTreeResponse>(
    `/v1/admin/factory/batches/${batchId}/merkle-tree`
  );
}

export async function retryBatch(batchId: string) {
  return fetchWithAuth<Record<string, unknown>>(`/v1/admin/system/batches/${batchId}/retry`, { method: "POST" });
}

export async function retryAnchor(anchorId: string) {
  return fetchWithAuth<Record<string, unknown>>(`/v1/admin/system/anchors/${anchorId}/retry`, { method: "POST" });
}

export interface Anchor {
  id: string;
  batch_id: string;
  merkle_root: string;
  product_count: number;
  status: string;
  transaction_id: string | null;
  block_number: number | null;
  created_at: string | null;
  anchored_at: string | null;
  error: string | null;
}

export async function listAnchors(params?: { skip?: number; limit?: number; status?: string; batch_id?: string }) {
  const sp = new URLSearchParams();
  if (params?.skip != null) sp.set("skip", String(params.skip));
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.status) sp.set("status", params.status);
  if (params?.batch_id) sp.set("batch_id", params.batch_id);
  const q = sp.toString();
  return fetchWithAuth<{ anchors: Anchor[]; total: number }>(`/v1/admin/factory/anchors${q ? `?${q}` : ""}`);
}

// Dashboard sub-stats
export async function getDashboardBatches(days = 30) {
  return fetchWithAuth<Record<string, unknown>>(
    `/v1/admin/dashboard/batches?days=${days}`
  );
}

export async function getDashboardScans(days = 30) {
  return fetchWithAuth<Record<string, unknown>>(
    `/v1/admin/dashboard/scans?days=${days}`
  );
}

// Analytics (Antifraud)
export async function getAnalyticsFraud(params?: {
  days?: number;
  min_risk_score?: number;
}) {
  const sp = new URLSearchParams();
  sp.set("days", String(params?.days ?? 30));
  sp.set("min_risk_score", String(params?.min_risk_score ?? 70));
  return fetchWithAuth<Record<string, unknown>>(
    `/v1/admin/analytics/fraud?${sp}`
  );
}

export async function getAnalyticsGeographic(days = 30) {
  return fetchWithAuth<Record<string, unknown>>(
    `/v1/admin/analytics/geographic?days=${days}`
  );
}

export async function getAnalyticsTrends(days = 30) {
  return fetchWithAuth<Record<string, unknown>>(
    `/v1/admin/analytics/trends?days=${days}`
  );
}

export async function getAnalyticsHeatmap(params?: { days?: number; min_risk?: number }) {
  const sp = new URLSearchParams();
  sp.set("days", String(params?.days ?? 7));
  sp.set("min_risk", String(params?.min_risk ?? 50));
  return fetchWithAuth<{ heatmap?: { day: number; hour: number; count: number }[] }>(
    `/v1/admin/analytics/heatmap?${sp}`
  );
}

export async function getAnalyticsScansPerMinute(hours = 24) {
  return fetchWithAuth<{ scans_per_minute?: { minute: string; count: number }[] }>(
    `/v1/admin/analytics/scans-per-minute?hours=${hours}`
  );
}

export async function getAnalyticsFraudsPerHour(days = 7) {
  return fetchWithAuth<{ frauds_per_hour?: { hour: string; count: number }[] }>(
    `/v1/admin/analytics/frauds-per-hour?days=${days}`
  );
}

export async function getAnalyticsRiskEvolution(days = 30) {
  return fetchWithAuth<{ risk_evolution?: { date: string; avg_risk: number; count: number }[] }>(
    `/v1/admin/analytics/risk-evolution?days=${days}`
  );
}

// Scans (individual)
export interface ScanItem {
  tag_id: string;
  product_id: string;
  batch_id: string | null;
  first_scan_at: string | null;
  scan_count: number;
  valid: boolean;
  status: string;
  risk_score: number;
  updated_at: string | null;
  product_name: string | null;
  product_token: string;
  country: string | null;
}

export async function listScans(params?: {
  skip?: number;
  limit?: number;
  product_id?: string;
  country?: string;
  risk_min?: number;
  risk_max?: number;
  days?: number;
  status?: string;
}) {
  const sp = new URLSearchParams();
  if (params?.skip != null) sp.set("skip", String(params.skip));
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.product_id) sp.set("product_id", params.product_id);
  if (params?.country) sp.set("country", params.country);
  if (params?.risk_min != null) sp.set("risk_min", String(params.risk_min));
  if (params?.risk_max != null) sp.set("risk_max", String(params.risk_max));
  if (params?.days != null) sp.set("days", String(params.days));
  if (params?.status) sp.set("status", params.status);
  const q = sp.toString();
  return fetchWithAuth<{ scans: ScanItem[]; total: number }>(
    `/v1/admin/scans${q ? `?${q}` : ""}`
  );
}

export async function blockScan(tagId: string) {
  return fetchWithAuth<{ message: string }>(`/v1/admin/scans/${tagId}/block`, { method: "POST" });
}

export async function observationScan(tagId: string) {
  return fetchWithAuth<{ message: string }>(`/v1/admin/scans/${tagId}/observation`, { method: "POST" });
}

export async function markFraudScan(tagId: string) {
  return fetchWithAuth<{ message: string }>(`/v1/admin/scans/${tagId}/fraud`, { method: "POST" });
}

export async function updateScanStatus(tagId: string, status: "ok" | "blocked" | "observation" | "fraud") {
  return fetchWithAuth<{ message: string }>(
    `/v1/admin/scans/${tagId}/status?status=${status}`,
    { method: "PATCH" }
  );
}

// Audit
export async function getAuditLogs(params?: {
  skip?: number;
  limit?: number;
  entity_type?: string;
  entity_id?: string;
  action?: string;
  user_id?: string;
  search?: string;
}) {
  const sp = new URLSearchParams();
  if (params?.skip != null) sp.set("skip", String(params.skip));
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.entity_type) sp.set("entity_type", params.entity_type);
  if (params?.entity_id) sp.set("entity_id", params.entity_id);
  if (params?.action) sp.set("action", params.action);
  if (params?.user_id) sp.set("user_id", params.user_id);
  if (params?.search) sp.set("search", params.search);
  const q = sp.toString();
  return fetchWithAuth<Record<string, unknown>[]>(
    `/v1/admin/audit/logs${q ? `?${q}` : ""}`
  );
}

// God Mode (super_admin only)
export async function getGodModeState() {
  return fetchWithAuth<{
    kill_switch: boolean;
    investigation_mode: boolean;
    max_alert_mode: boolean;
    risk_limit: number;
    blocked_countries: string[];
  }>("/v1/admin/god-mode/state");
}

export async function setKillSwitch(active: boolean) {
  return fetchWithAuth<{ message: string; active: boolean }>("/v1/admin/god-mode/kill-switch", {
    method: "POST",
    body: JSON.stringify({ active }),
  });
}

export async function setInvestigationMode(active: boolean) {
  return fetchWithAuth<{ message: string; active: boolean }>("/v1/admin/god-mode/investigation", {
    method: "POST",
    body: JSON.stringify({ active }),
  });
}

export async function setMaxAlertMode(active: boolean) {
  return fetchWithAuth<{ message: string; active: boolean }>("/v1/admin/god-mode/max-alert", {
    method: "POST",
    body: JSON.stringify({ active }),
  });
}

export async function setRiskLimit(limit: number) {
  return fetchWithAuth<{ message: string; risk_limit: number }>("/v1/admin/god-mode/risk-limit", {
    method: "POST",
    body: JSON.stringify({ limit }),
  });
}

export async function blockCountry(country: string) {
  return fetchWithAuth<{ message: string }>("/v1/admin/god-mode/block-country", {
    method: "POST",
    body: JSON.stringify({ country }),
  });
}

export async function unblockCountry(country: string) {
  return fetchWithAuth<{ message: string }>("/v1/admin/god-mode/unblock-country", {
    method: "POST",
    body: JSON.stringify({ country }),
  });
}

export async function invalidateAllJwt() {
  return fetchWithAuth<{ message: string }>("/v1/admin/god-mode/invalidate-all-jwt", {
    method: "POST",
  });
}

export async function exportAuditLogs(format: "csv" | "json" = "csv", entity_type?: string): Promise<Blob> {
  const token = getToken();
  const sp = new URLSearchParams({ format });
  if (entity_type) sp.set("entity_type", entity_type);
  const res = await fetch(`${BASE_URL}/v1/admin/audit/export?${sp}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error("Export failed");
  return res.blob();
}

export { getToken, clearToken };
