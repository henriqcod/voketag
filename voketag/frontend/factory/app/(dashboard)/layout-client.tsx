"use client";

import { LayoutProvider, useLayout } from "@/lib/layout-context";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { HeaderSync } from "@/components/layout/HeaderSync";

export function DashboardLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <LayoutProvider>
      <HeaderSync />
      <div className="flex min-h-screen bg-graphite-50 dark:bg-graphite-950">
        <Sidebar />
        <ContentArea>{children}</ContentArea>
      </div>
    </LayoutProvider>
  );
}

function HeaderWithContext() {
  const { headerTitle, headerBreadcrumbs, headerStatus } = useLayout();
  return <Header title={headerTitle} breadcrumbs={headerBreadcrumbs} status={headerStatus} />;
}

function ContentArea({ children }: { children: React.ReactNode }) {
  const { sidebarCollapsed } = useLayout();
  return (
    <div
      className="flex flex-1 flex-col transition-[margin-left] duration-300"
      style={{ marginLeft: sidebarCollapsed ? 80 : 256 }}
    >
      <HeaderWithContext />
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
