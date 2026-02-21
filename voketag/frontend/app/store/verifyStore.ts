import { create } from "zustand";

export type VerifyStatus = "original" | "warning" | "fake";

export interface VerifyProduct {
  name: string;
  batch: string;
  factory: string;
  manufactured_at: string;
}

export interface VerifyState {
  status: VerifyStatus | null;
  product: VerifyProduct | null;
  scanCount: number;
  firstScanAt: string | null;
  riskScore: number;
  lastScannedCode: string | null;
  loading: boolean;
  error: string | null;
}

interface VerifyActions {
  setLoading: (v: boolean) => void;
  setError: (v: string | null) => void;
  setResult: (data: {
    status: VerifyStatus;
    product?: VerifyProduct | null;
    scan_count?: number;
    first_scan_at?: string | null;
    risk_score?: number;
    lastScannedCode?: string | null;
  }) => void;
  reset: () => void;
}

const initialState: VerifyState = {
  status: null,
  product: null,
  scanCount: 0,
  firstScanAt: null,
  riskScore: 0,
  lastScannedCode: null,
  loading: false,
  error: null,
};

export const useVerifyStore = create<VerifyState & VerifyActions>((set) => ({
  ...initialState,
  setLoading: (loading) => set({ loading, error: loading ? null : undefined }),
  setError: (error) => set({ error, loading: false }),
  setResult: (data) =>
    set({
      status: data.status,
      product: data.product ?? null,
      scanCount: data.scan_count ?? 0,
      firstScanAt: data.first_scan_at ?? null,
      riskScore: data.risk_score ?? 0,
      lastScannedCode: data.lastScannedCode ?? null,
      loading: false,
      error: null,
    }),
  reset: () => set(initialState),
}));
