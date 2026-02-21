"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

interface ResetPasswordModalProps {
  open: boolean;
  user: { id: string; email: string } | null;
  onClose: () => void;
  onReset: (newPassword: string) => Promise<void>;
  loading?: boolean;
}

export function ResetPasswordModal({ open, user, onClose, onReset, loading }: ResetPasswordModalProps) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm || password.length < 8) return;
    await onReset(password);
    setPassword("");
    setConfirm("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-xl border border-[#334155] bg-[#1e293b] p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-[#f8fafc]">Resetar senha - {user?.email}</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="mb-2 block text-sm text-[#94a3b8]">Nova senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              className="w-full rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-[#f8fafc] focus:border-blue-500 focus:outline-none"
              required
            />
          </div>
          <div className="mb-6">
            <label className="mb-2 block text-sm text-[#94a3b8]">Confirmar senha</label>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              minLength={8}
              className="w-full rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-[#f8fafc] focus:border-blue-500 focus:outline-none"
              required
            />
            {password && confirm && password !== confirm && (
              <p className="mt-1 text-sm text-red-400">As senhas não coincidem</p>
            )}
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={loading || password.length < 8 || password !== confirm}
            >
              {loading ? "Salvando..." : "Alterar senha"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
