"use client";

import { useRouter } from "next/navigation";
import { clearToken } from "@/lib/api-client";

type SystemStatus = "ok" | "degraded" | "critical";

interface TopbarProps {
  userEmail?: string;
  systemStatus?: SystemStatus;
}

export function Topbar({ userEmail, systemStatus = "ok" }: TopbarProps) {
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  const statusIndicator =
    systemStatus === "ok"
      ? "🟢"
      : systemStatus === "degraded"
      ? "🟡"
      : "🔴";

  const statusLabel =
    systemStatus === "ok"
      ? "Operacional"
      : systemStatus === "degraded"
      ? "Degradado"
      : "Crítico";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-[#334155] bg-[#1e293b] px-6">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-2 text-sm">
          <span>{statusIndicator}</span>
          <span className="text-[#94a3b8]">{statusLabel}</span>
        </span>
      </div>
      <div className="flex items-center gap-4">
        {userEmail && (
          <span className="text-sm text-[#94a3b8]">{userEmail}</span>
        )}
        <button
          onClick={handleLogout}
          className="rounded-lg px-3 py-2 text-sm text-[#94a3b8] transition-colors hover:bg-[#334155] hover:text-[#f8fafc]"
        >
          Sair
        </button>
      </div>
    </header>
  );
}
