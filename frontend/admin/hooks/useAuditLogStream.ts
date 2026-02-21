"use client";

import { useCallback, useRef, useState } from "react";
import { getToken } from "@/lib/api-client";

const BASE_URL =
  typeof window !== "undefined"
    ? "/api/admin"
    : (process.env.NEXT_PUBLIC_ADMIN_API || "http://127.0.0.1:8082");

export interface AuditLogEntry {
  id?: string;
  entity_type?: string;
  entity_id?: string;
  action?: string;
  user_id?: string;
  changes?: string;
  created_at?: string;
  [key: string]: unknown;
}

interface UseAuditLogStreamOptions {
  entityType?: string;
  action?: string;
  onLog: (log: AuditLogEntry) => void;
  onError?: (err: Error) => void;
}

export function useAuditLogStream() {
  const abortRef = useRef<AbortController | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(
    (options: UseAuditLogStreamOptions) => {
      if (abortRef.current) return;
      const { entityType, action, onLog, onError } = options;
      const token = getToken();
      if (!token) {
        onError?.(new Error("Não autenticado"));
        return;
      }
      const params = new URLSearchParams();
      if (entityType) params.set("entity_type", entityType);
      if (action) params.set("action", action);
      const url = `${BASE_URL}/v1/admin/audit/logs/stream${params.toString() ? `?${params}` : ""}`;
      const controller = new AbortController();
      abortRef.current = controller;
      setIsConnected(true);

      fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
        credentials: "include",
        signal: controller.signal,
      })
        .then(async (res) => {
          if (!res.ok || !res.body) {
            throw new Error(`Stream failed: ${res.status}`);
          }
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const blocks = buffer.split("\n\n");
            buffer = blocks.pop() ?? "";
            for (const block of blocks) {
              let eventType = "";
              for (const line of block.split("\n")) {
                if (line.startsWith("event: ")) {
                  eventType = line.slice(7).trim();
                } else if (line.startsWith("data: ") && eventType === "log") {
                  try {
                    const data = JSON.parse(line.slice(6)) as AuditLogEntry;
                    onLog(data);
                  } catch {
                    // ignore parse errors
                  }
                }
              }
            }
          }
        })
        .catch((err) => {
          if (err.name !== "AbortError") {
            onError?.(err instanceof Error ? err : new Error(String(err)));
          }
        })
        .finally(() => {
          abortRef.current = null;
          setIsConnected(false);
        });
    },
    []
  );

  const disconnect = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
      setIsConnected(false);
    }
  }, []);

  return { connect, disconnect, isConnected };
}
