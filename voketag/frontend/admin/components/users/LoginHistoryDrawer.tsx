"use client";

import { useEffect, useState } from "react";
import { getLoginHistory } from "@/lib/api-client";

interface LoginHistoryDrawerProps {
  open: boolean;
  user: { id: string; email: string } | null;
  onClose: () => void;
}

interface LogEntry {
  id: string;
  ip_address: string | null;
  user_agent: string;
  created_at: string;
}

export function LoginHistoryDrawer({ open, user, onClose }: LoginHistoryDrawerProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && user) {
      setLoading(true);
      getLoginHistory(user.id)
        .then(setLogs)
        .finally(() => setLoading(false));
    }
  }, [open, user]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative w-full max-w-md border-l border-[#334155] bg-[#1e293b] shadow-xl">
        <div className="flex items-center justify-between border-b border-[#334155] p-4">
          <h2 className="text-lg font-semibold text-[#f8fafc]">
            Histórico de login - {user?.email}
          </h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-[#94a3b8] hover:bg-[#334155]"
          >
            ✕
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto p-4">
          {loading ? (
            <p className="text-[#94a3b8]">Carregando...</p>
          ) : logs.length === 0 ? (
            <p className="text-[#94a3b8]">Nenhum registro.</p>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="rounded-lg border border-[#334155] bg-[#0f172a] p-3 text-sm"
                >
                  <p className="text-[#f8fafc]">
                    {new Date(log.created_at).toLocaleString("pt-BR")}
                  </p>
                  <p className="text-[#94a3b8]">IP: {log.ip_address ?? "-"}</p>
                  <p className="mt-1 truncate text-xs text-[#64748b]" title={log.user_agent}>
                    {log.user_agent || "-"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
