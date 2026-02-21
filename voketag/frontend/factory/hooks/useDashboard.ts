import { useQuery } from "@tanstack/react-query";
import { fetchDashboardMetrics } from "@/lib/api/dashboard";

export function useDashboardMetrics() {
  return useQuery({
    queryKey: ["dashboard", "metrics"],
    queryFn: fetchDashboardMetrics,
    staleTime: 30_000,
  });
}
