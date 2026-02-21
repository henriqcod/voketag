"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useState } from "react";
import { Button } from "@nextui-org/react";
import { Home, Users2, Layers, ShieldCheck, Menu } from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/users", label: "Usuários", icon: Users2 },
  { href: "/factory", label: "Factory", icon: Layers },
  { href: "/scans", label: "Scans", icon: Home },
  { href: "/antifraud", label: "Antifraude", icon: ShieldCheck },
  { href: "/audit", label: "Auditoria", icon: Home },
  { href: "/monitoring", label: "Monitoramento", icon: Home },
  { href: "/settings", label: "Configurações", icon: Home },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`fixed left-0 top-0 z-40 h-screen transition-all duration-300 bg-slate-900 text-slate-100 border-r border-slate-800 ${
        collapsed ? "w-20" : "w-56"
      }`}
    >
      <div className="flex h-16 items-center justify-between px-4">
        <Link href="/dashboard" className={`text-lg font-semibold ${collapsed ? "hidden" : ""}`}>
          VokeTag Admin
        </Link>
        <Button auto light onClick={() => setCollapsed((s) => !s)} aria-label="toggle menu">
          <Menu className="w-4 h-4" />
        </Button>
      </div>

      <div className="h-px bg-slate-800" />

      <nav className="flex-1 overflow-y-auto p-2 pt-3">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname?.startsWith(item.href + "/");
            const IconComp = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`group flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-slate-800 transition-colors ${
                    active ? "bg-slate-800 font-medium" : "text-slate-300"
                  }`}
                >
                  <IconComp className="w-4 h-4" />
                  <span className={`${collapsed ? "hidden" : ""}`}>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
