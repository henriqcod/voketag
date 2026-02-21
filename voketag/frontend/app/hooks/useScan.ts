"use client";

import { useState } from "react";
import { fetchScan } from "@/lib/api-client";

export interface ScanResult {
  valid: boolean;
  product_id: string;
  batch_id: string;
  scan_count: number;
  message?: string;
  timestamp?: string;
}

export function useScan() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);

  const scanTag = async (tagId: string) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await fetchScan(tagId);
      setResult({
        valid: data.valid || true,
        product_id: data.product_id || "N/A",
        batch_id: data.batch_id || "N/A",
        scan_count: data.scan_count || 1,
        message: data.message,
        timestamp: data.timestamp,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao escanear tag");
    } finally {
      setLoading(false);
    }
  };

  const clearResult = () => {
    setResult(null);
    setError(null);
  };

  return {
    scanTag,
    loading,
    error,
    result,
    clearResult,
  };
}