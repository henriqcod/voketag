"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { useLayout } from "@/lib/layout-context";

const ROUTE_CONFIG: Record<string, { title: string }> = {
  "/dashboard": { title: "Dashboard" },
  "/batches/anchor": { title: "Registro de Lotes" },
  "/batches": { title: "Lotes" },
  "/scans": { title: "Scans" },
  "/exports": { title: "Exportar NTAG" },
  "/audit": { title: "Auditoria" },
  "/settings": { title: "Configurações" },
};

function getConfig(pathname: string) {
  if (ROUTE_CONFIG[pathname]) return ROUTE_CONFIG[pathname];
  if (pathname.startsWith("/batches/") && pathname !== "/batches/anchor") {
    const id = pathname.split("/")[2];
    return { title: `Lote ${id?.slice(0, 8) ?? "..."}` };
  }
  return { title: "Portal da Fábrica" };
}

export function HeaderSync() {
  const pathname = usePathname();
  const { setHeader } = useLayout();

  useEffect(() => {
    const config = getConfig(pathname);
    setHeader({ title: config.title, breadcrumbs: [] });
  }, [pathname, setHeader]);

  return null;
}
