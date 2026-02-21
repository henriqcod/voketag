"use client";

import { createContext, useContext, useSyncExternalStore } from "react";
import { getRoleFromJwt } from "@/lib/auth-cookies";

export type Role = "admin" | "operador";

type PermissionsContextType = {
  role: Role;
  canAnchor: boolean;
  canExport: boolean;
  canManageBatches: boolean;
  canViewAudit: boolean;
  canManageSettings: boolean;
};

const PermissionsContext = createContext<PermissionsContextType | null>(null);

const adminPermissions = {
  role: "admin" as Role,
  canAnchor: true,
  canExport: true,
  canManageBatches: true,
  canViewAudit: true,
  canManageSettings: true,
};

const operadorPermissions = {
  role: "operador" as Role,
  canAnchor: true,
  canExport: true,
  canManageBatches: true,
  canViewAudit: false,
  canManageSettings: false,
};

function getRoleFromStorage(): Role {
  if (typeof window === "undefined") return "operador";
  const r = localStorage.getItem("voketag_role");
  if (r === "admin") return "admin";
  if (r === "operador") return "operador";
  const token = localStorage.getItem("voketag_token");
  if (token) {
    try {
      const role = getRoleFromJwt(token);
      localStorage.setItem("voketag_role", role);
      return role;
    } catch {}
  }
  return "operador";
}

function subscribeToRole(cb: () => void) {
  const handler = () => cb();
  window.addEventListener("storage", handler);
  return () => window.removeEventListener("storage", handler);
}

export function PermissionsProvider({ children }: { children: React.ReactNode }) {
  const role = useSyncExternalStore(subscribeToRole, getRoleFromStorage, () => "operador");
  const permissions = role === "admin" ? adminPermissions : operadorPermissions;

  return (
    <PermissionsContext.Provider value={permissions}>
      {children}
    </PermissionsContext.Provider>
  );
}

export function usePermissions() {
  const ctx = useContext(PermissionsContext);
  return ctx ?? adminPermissions;
}
