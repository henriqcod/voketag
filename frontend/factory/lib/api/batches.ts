import { apiFetch } from "./client";

export interface Batch {
  id: string;
  status: string;
  product_count: number;
  blockchain_tx?: string | null;
  merkle_root?: string | null;
  error?: string | null;
  created_at: string;
  processing_completed_at?: string | null;
  anchored_at?: string | null;
}

export interface BatchCreateRequest {
  product_count: number;
  product_name?: string;
  category?: string;
  metadata?: Record<string, unknown>;
}

export interface BatchCreateResponse {
  batch_id: string;
  job_id: string;
  status: string;
  product_count: number;
  estimated_completion: string;
  message: string;
}

export interface BatchStatusResponse {
  batch_id: string;
  status: string;
  product_count: number;
  created_at: string;
  processing_completed_at?: string | null;
  anchored_at?: string | null;
  blockchain_tx?: string | null;
  merkle_root?: string | null;
  error?: string | null;
  celery_task_id?: string | null;
}

export interface ListBatchesParams {
  skip?: number;
  limit?: number;
  status?: string;
  risk?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export async function listBatches(params?: ListBatchesParams): Promise<Batch[]> {
  const sp = new URLSearchParams();
  if (params?.skip != null) sp.set("skip", String(params.skip));
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.status) sp.set("status", params.status);
  if (params?.risk) sp.set("risk", params.risk);
  if (params?.date_from) sp.set("date_from", params.date_from);
  if (params?.date_to) sp.set("date_to", params.date_to);
  if (params?.search) sp.set("search", params.search);
  const q = sp.toString();
  return apiFetch<Batch[]>(`/batches${q ? `?${q}` : ""}`);
}

export async function getBatch(batchId: string): Promise<Batch> {
  return apiFetch<Batch>(`/batches/${batchId}`);
}

export async function getBatchStatus(
  batchId: string
): Promise<BatchStatusResponse> {
  return apiFetch<BatchStatusResponse>(`/batches/${batchId}/status`);
}

export async function createBatch(
  data: BatchCreateRequest
): Promise<BatchCreateResponse> {
  return apiFetch<BatchCreateResponse>("/batches", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function uploadBatchCsv(
  batchId: string,
  file: File
): Promise<{ message?: string; [k: string]: unknown }> {
  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/v1";
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("voketag_token")
      : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/batches/${batchId}/csv`, {
    method: "POST",
    headers,
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function retryBatch(batchId: string): Promise<{ message: string }> {
  return apiFetch(`/batches/${batchId}/retry`, { method: "POST" });
}

export interface BatchProduct {
  serial_number: string;
  product_code?: string;
  batch_id: string;
  qr_code_url?: string;
  nfc_payload?: string;
  blockchain_hash?: string;
  verification_url?: string;
}

export async function getBatchProducts(batchId: string): Promise<BatchProduct[]> {
  try {
    return await apiFetch<BatchProduct[]>(`/batches/${batchId}/products`);
  } catch {
    return [];
  }
}

export interface AntifraudEvent {
  id: string;
  type: string;
  timestamp: string;
  details?: Record<string, unknown>;
  severity?: "low" | "medium" | "high";
}

export async function getBatchAntifraudEvents(batchId: string): Promise<AntifraudEvent[]> {
  try {
    return await apiFetch<AntifraudEvent[]>(`/batches/${batchId}/antifraud-events`);
  } catch {
    return [];
  }
}
