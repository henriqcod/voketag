"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/users", label: "Usuários", icon: "👤" },
  { href: "/factory", label: "Factory", icon: "🏭" },
  { href: "/scans", label: "Scans", icon: "📱" },
  { href: "/antifraud", label: "Antifraude", icon: "🛡️" },
  { href: "/audit", label: "Auditoria", icon: "📋" },
  { href: "/monitoring", label: "Monitoramento", icon: "📡" },
  { href: "/settings", label: "Configurações", icon: "⚙️" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-56 border-r border-[#334155] bg-[#1e293b]">
      <div className="flex h-full flex-col">
        <div className="border-b border-[#334155] px-4 py-5">
          <Link href="/dashboard" className="text-xl font-bold text-[#f8fafc]">
            VokeTag Admin
          </Link>
        </div>
        <nav className="flex-1 space-y-0.5 p-3">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-brand-500/20 text-[#f8fafc]"
                    : "text-[#94a3b8] hover:bg-[#334155]/50 hover:text-[#f8fafc]"
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
