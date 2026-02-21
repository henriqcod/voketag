"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ThemeProvider } from "@/lib/theme-context";
import { ToastProvider } from "@/lib/toast-context";
import { PermissionsProvider } from "@/lib/permissions-context";
import { TenantProvider } from "@/lib/tenant-context";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TenantProvider>
          <PermissionsProvider>
            <ToastProvider>{children}</ToastProvider>
          </PermissionsProvider>
        </TenantProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
