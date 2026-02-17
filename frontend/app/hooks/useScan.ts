"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api-client";

export interface ScanResult {
  tag_id: string;
  product_id: string;
  batch_id: string;
  first_scan_at?: string;
  scan_count: number;
  valid: boolean;
}

export function useScan() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);

  const scanTag = async (tagId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<ScanResult>(`/v1/scan/${tagId}`);
      setResult(data);
      return data;
    } catch (e) {
      const message = e instanceof Error ? e.message : "Scan failed";
      setError(message);
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  return { scanTag, loading, error, result, reset };
}
