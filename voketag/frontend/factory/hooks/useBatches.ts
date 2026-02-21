import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { ListBatchesParams } from "@/lib/api/batches";
import {
  listBatches,
  getBatch,
  getBatchStatus,
  createBatch,
  uploadBatchCsv,
  retryBatch,
  getBatchProducts,
  getBatchAntifraudEvents,
} from "@/lib/api/batches";

export function useBatchesList(params?: ListBatchesParams) {
  return useQuery({
    queryKey: ["batches", "list", params],
    queryFn: () => listBatches(params),
  });
}

export function useBatch(batchId: string | null) {
  return useQuery({
    queryKey: ["batch", batchId],
    queryFn: () => getBatch(batchId!),
    enabled: !!batchId,
  });
}

export function useBatchStatus(batchId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["batch", batchId, "status"],
    queryFn: () => getBatchStatus(batchId!),
    enabled: !!batchId && enabled,
  });
}

export function useCreateBatch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createBatch,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["batches"] }),
  });
}

export function useUploadBatchCsv(batchId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadBatchCsv(batchId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["batch", batchId] });
      qc.invalidateQueries({ queryKey: ["batches"] });
    },
  });
}

export function useRetryBatch(options?: { onSuccess?: () => void }) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (batchId: string) => retryBatch(batchId),
    onSuccess: (_, batchId) => {
      qc.invalidateQueries({ queryKey: ["batch", batchId] });
      qc.invalidateQueries({ queryKey: ["batches"] });
      options?.onSuccess?.();
    },
  });
}

export function useBatchProducts(batchId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["batch", batchId, "products"],
    queryFn: () => getBatchProducts(batchId!),
    enabled: !!batchId && enabled,
  });
}

export function useBatchAntifraudEvents(batchId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["batch", batchId, "antifraud"],
    queryFn: () => getBatchAntifraudEvents(batchId!),
    enabled: !!batchId && enabled,
  });
}
