"use client";

import { createContext, useContext, useState, useCallback } from "react";

type LayoutContextType = {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;
  toggleSidebar: () => void;
  headerTitle: string;
  headerBreadcrumbs: { label: string; href?: string }[];
  headerStatus: "online" | "degraded" | "offline";
  setHeader: (config: {
    title?: string;
    breadcrumbs?: { label: string; href?: string }[];
    status?: "online" | "degraded" | "offline";
  }) => void;
};

const LayoutContext = createContext<LayoutContextType | null>(null);

export function LayoutProvider({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [headerTitle, setHeaderTitle] = useState("Portal da Fábrica");
  const [headerBreadcrumbs, setHeaderBreadcrumbs] = useState<{ label: string; href?: string }[]>([]);
  const [headerStatus, setHeaderStatus] = useState<"online" | "degraded" | "offline">("online");

  const setHeader = useCallback((config: { title?: string; breadcrumbs?: { label: string; href?: string }[]; status?: "online" | "degraded" | "offline" }) => {
    if (config.title != null) setHeaderTitle(config.title);
    if (config.breadcrumbs != null) setHeaderBreadcrumbs(config.breadcrumbs);
    if (config.status != null) setHeaderStatus(config.status);
  }, []);

  const toggleSidebar = useCallback(() => setSidebarCollapsed((c) => !c), []);

  return (
    <LayoutContext.Provider
      value={{
        sidebarCollapsed,
        setSidebarCollapsed,
        toggleSidebar,
        headerTitle,
        headerBreadcrumbs,
        headerStatus,
        setHeader,
      }}
    >
      {children}
    </LayoutContext.Provider>
  );
}

export function useLayout() {
  const ctx = useContext(LayoutContext);
  if (!ctx) throw new Error("useLayout must be used within LayoutProvider");
  return ctx;
}
