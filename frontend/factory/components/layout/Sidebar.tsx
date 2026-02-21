"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLayout } from "@/lib/layout-context";
import { usePermissions } from "@/lib/permissions-context";

const navItems: { href: string; label: string; icon: string; show: (p: { canViewAudit: boolean; canManageSettings: boolean }) => boolean }[] = [
  { href: "/dashboard", label: "Dashboard", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6", show: () => true },
  { href: "/batches/anchor", label: "Registro de Lotes", icon: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12", show: () => true },
  { href: "/batches", label: "Lotes", icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10", show: () => true },
  { href: "/scans", label: "Scans", icon: "M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z", show: () => true },
  { href: "/exports", label: "Exportar NTAG", icon: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4", show: () => true },
  { href: "/audit", label: "Auditoria", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01", show: (p) => p.canViewAudit },
  { href: "/settings", label: "Configurações", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z", show: (p) => p.canManageSettings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed: collapsed, setSidebarCollapsed } = useLayout();
  const permissions = usePermissions();
  const visibleItems = navItems.filter((item) => item.show(permissions));

  return (
    <aside
      className={`font-sidebar fixed left-0 top-0 z-40 h-screen border-r border-graphite-200 bg-white shadow-card transition-all duration-300 dark:border-graphite-800 dark:bg-graphite-900 ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center justify-between border-b border-graphite-200 px-4 dark:border-graphite-800">
          {!collapsed && (
            <Link href="/dashboard" className="flex items-center gap-2">
              <span className="text-xl font-bold text-primary-600 dark:text-primary-400">VokeTag</span>
              <span className="text-xs text-graphite-500 dark:text-graphite-400">Factory</span>
            </Link>
          )}
          <button
            type="button"
            onClick={() => setSidebarCollapsed(!collapsed)}
            className="rounded-lg p-2 text-graphite-500 hover:bg-graphite-100 dark:hover:bg-graphite-800 dark:hover:text-graphite-300"
            aria-label={collapsed ? "Expandir sidebar" : "Recolher sidebar"}
          >
            <svg className={`h-5 w-5 transition-transform ${collapsed ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {visibleItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-50 text-primary-600 dark:bg-primary-500/12 dark:text-primary-400"
                    : "text-graphite-600 hover:bg-graphite-100 dark:text-graphite-400 dark:hover:bg-white/5 dark:hover:text-graphite-300"
                } ${collapsed ? "justify-center" : ""}`}
                title={collapsed ? item.label : undefined}
              >
                <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                </svg>
                {!collapsed && item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-graphite-200 px-4 py-3 dark:border-graphite-800">
          <p className={`text-xs text-graphite-500 dark:text-graphite-400 ${collapsed ? "text-center" : ""}`}>v1.0 Premium</p>
        </div>
      </div>
    </aside>
  );
}
