import { useQuery } from "@tanstack/react-query";
import { fetchScans, fetchScanDetail } from "@/lib/api/scans";
import type { ScansFilters } from "@/lib/api/scans";

export type { ScansFilters };

export function useScans(filters?: ScansFilters, options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: ["scans", filters],
    queryFn: () => fetchScans(filters),
    refetchInterval: options?.refetchInterval ?? 5000,
  });
}

export function useScanDetail(scanId: string | null) {
  return useQuery({
    queryKey: ["scan", scanId],
    queryFn: () => fetchScanDetail(scanId!),
    enabled: !!scanId,
  });
}
