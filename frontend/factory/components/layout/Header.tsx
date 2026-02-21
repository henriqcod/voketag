"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTheme } from "@/lib/theme-context";
import { clearAuthCookies } from "@/lib/auth-cookies";
import { useTenant } from "@/lib/tenant-context";

type SystemStatus = "online" | "degraded" | "offline";

export function Header({
  title,
  status = "online",
}: {
  title: string;
  breadcrumbs?: { label: string; href?: string }[];
  status?: SystemStatus;
}) {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { tenantName, isMultiTenant } = useTenant();

  const handleLogout = () => {
    clearAuthCookies();
    router.push("/login");
  };

  const statusConfig: Record<SystemStatus, { label: string; color: string }> = {
    online: { label: "Online", color: "bg-success" },
    degraded: { label: "Degradado", color: "bg-amber-500" },
    offline: { label: "Offline", color: "bg-alert" },
  };
  const sc = statusConfig[status];

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-graphite-200 bg-white/95 px-8 backdrop-blur dark:border-graphite-800 dark:bg-graphite-950/95">
      <div className="flex items-center gap-6">
        {isMultiTenant && tenantName && (
          <span className="rounded-md bg-graphite-100 px-2 py-1 text-xs font-medium text-graphite-600 dark:bg-graphite-800 dark:text-graphite-300">
            {tenantName}
          </span>
        )}
        <h1 className="text-lg font-semibold text-graphite-900 dark:text-white">
          {title}
        </h1>
      </div>
      <div className="flex items-center gap-4">
        <div
          className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs ${
            status === "online"
              ? "bg-success/10 text-success dark:bg-success/20"
              : status === "degraded"
              ? "bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400"
              : "bg-alert/10 text-alert dark:bg-alert/20"
          }`}
        >
          <span className={`h-2 w-2 rounded-full ${sc.color} ${status === "online" ? "animate-pulse" : ""}`} />
          {sc.label}
        </div>
        <button
          type="button"
          onClick={toggleTheme}
          className="rounded-lg p-2 text-graphite-600 hover:bg-graphite-100 dark:text-graphite-400 dark:hover:bg-graphite-800"
          aria-label={theme === "dark" ? "Modo claro" : "Modo escuro"}
        >
          {theme === "dark" ? (
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>
        <div className="h-8 w-px bg-graphite-200 dark:bg-graphite-700" />
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg px-3 py-1.5 text-sm text-graphite-600 hover:bg-graphite-100 dark:text-graphite-400 dark:hover:bg-graphite-800 dark:hover:text-white"
        >
          Sair
        </button>
      </div>
    </header>
  );
}
