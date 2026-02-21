"use client";

import { createContext, useContext } from "react";

type TenantContextType = {
  tenantId: string | null;
  tenantName: string | null;
  isMultiTenant: boolean;
};

const TenantContext = createContext<TenantContextType>({
  tenantId: "default",
  tenantName: "Fábrica Principal",
  isMultiTenant: false,
});

export function TenantProvider({
  children,
  tenantId = "default",
  tenantName = "Fábrica Principal",
  isMultiTenant = false,
}: {
  children: React.ReactNode;
  tenantId?: string | null;
  tenantName?: string | null;
  isMultiTenant?: boolean;
}) {
  return (
    <TenantContext.Provider value={{ tenantId, tenantName, isMultiTenant }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
