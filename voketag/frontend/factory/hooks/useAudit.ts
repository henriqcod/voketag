import { useQuery } from "@tanstack/react-query";
import { fetchLogs } from "@/lib/api/logs";
import type { LogsFilters } from "@/lib/api/logs";

export function useAuditLogs(filters?: LogsFilters) {
  return useQuery({
    queryKey: ["audit", "logs", filters],
    queryFn: () => fetchLogs(filters),
  });
}
