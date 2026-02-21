"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/ui/Sidebar";
import { Topbar } from "@/components/ui/Topbar";
import { getToken, getSystemStatus } from "@/lib/api-client";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [userEmail, setUserEmail] = useState<string | undefined>();
  const [systemStatus, setSystemStatus] = useState<"ok" | "degraded" | "critical">("ok");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    try {
      const payload = JSON.parse(atob(token.split(".")[1] ?? "{}"));
      setUserEmail((payload.email as string) ?? undefined);
    } catch {
      // ignore
    }
    setReady(true);
  }, [router]);

  useEffect(() => {
    if (!ready) return;
    getSystemStatus()
      .then((r) => {
        const services = r.services ?? [];
        const okCount = services.filter((s) => s.status === "ok").length;
        if (okCount === services.length && services.length > 0) setSystemStatus("ok");
        else if (okCount === 0) setSystemStatus("critical");
        else setSystemStatus("degraded");
      })
      .catch(() => setSystemStatus("critical"));
  }, [ready]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0f172a]">
        <p className="text-[#94a3b8]">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#0f172a]">
      <Sidebar />
      <div className="ml-56 flex flex-1 flex-col">
        <Topbar userEmail={userEmail} systemStatus={systemStatus} />
        <main className="flex-1 p-6">
          <Suspense fallback={<div className="flex min-h-[200px] items-center justify-center"><p className="text-[#94a3b8]">Carregando...</p></div>}>
            {children}
          </Suspense>
        </main>
      </div>
    </div>
  );
}
