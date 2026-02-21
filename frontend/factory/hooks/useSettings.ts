import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchSettings, saveSettings } from "@/lib/api/settings";

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
  });
}

export function useSaveSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: saveSettings,
    onSuccess: (data) => qc.setQueryData(["settings"], data),
  });
}
