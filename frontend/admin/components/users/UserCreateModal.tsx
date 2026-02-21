"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import type { UserCreate as UserCreateData } from "@/types/admin";

interface UserCreateModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: UserCreateData) => Promise<void>;
  loading?: boolean;
}

const ROLES = [
  { value: "viewer", label: "Viewer" },
  { value: "factory_manager", label: "FactoryManager" },
  { value: "compliance", label: "Compliance" },
  { value: "admin", label: "Admin" },
  { value: "super_admin", label: "SuperAdmin" },
];

export function UserCreateModal({ open, onClose, onSave, loading }: UserCreateModalProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("viewer");

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave({ name, email, role, password });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-xl border border-[#334155] bg-[#1e293b] p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-[#f8fafc]">Criar novo usuário</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="mb-2 block text-sm text-[#94a3b8]">Nome</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-[#f8fafc] focus:border-blue-500 focus:outline-none"
              required
            />
          </div>
          <div className="mb-4">
            <label className="mb-2 block text-sm text-[#94a3b8]">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-[#f8fafc] focus:border-blue-500 focus:outline-none"
              required
            />
          </div>
          <div className="mb-4">
            <label className="mb-2 block text-sm text-[#94a3b8]">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-[#f8fafc] focus:border-blue-500 focus:outline-none"
              required
              minLength={8}
            />
          </div>
          <div className="mb-6">
            <label className="mb-2 block text-sm text-[#94a3b8]">Papel</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-[#f8fafc] focus:border-blue-500 focus:outline-none"
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Criando..." : "Criar"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
