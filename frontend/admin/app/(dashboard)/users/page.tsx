"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/Table";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { UserEditModal } from "@/components/users/UserEditModal";
import { ResetPasswordModal } from "@/components/users/ResetPasswordModal";
import { LoginHistoryDrawer } from "@/components/users/LoginHistoryDrawer";
import { useDebounce } from "@/hooks/useDebounce";
import {
  listUsers,
  deleteUser,
  updateUser,
  blockUser,
  unblockUser,
  adminResetPassword,
  forceLogoutUser,
} from "@/lib/api-client";
import type { User } from "@/types/admin";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; email: string } | null>(null);
  const [confirmForceLogout, setConfirmForceLogout] = useState<{ id: string; email: string } | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [forceLogoutLoading, setForceLogoutLoading] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [editLoading, setEditLoading] = useState(false);
  const [resetUser, setResetUser] = useState<{ id: string; email: string } | null>(null);
  const [resetLoading, setResetLoading] = useState(false);
  const [loginHistoryUser, setLoginHistoryUser] = useState<{ id: string; email: string } | null>(null);

  const searchDebounced = useDebounce(search, 400);

  const loadUsers = useCallback(() => {
    setLoading(true);
    listUsers({ skip: page * 50, limit: 50, role: roleFilter || undefined, search: searchDebounced || undefined })
      .then(setUsers)
      .catch((e) => setError(e instanceof Error ? e.message : "Erro"))
      .finally(() => setLoading(false));
  }, [page, roleFilter, searchDebounced]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  async function handleConfirmDelete() {
    if (!confirmDelete) return;
    setDeleteLoading(true);
    try {
      await deleteUser(confirmDelete.id);
      setConfirmDelete(null);
      loadUsers();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao excluir");
    } finally {
      setDeleteLoading(false);
    }
  }

  async function handleConfirmForceLogout() {
    if (!confirmForceLogout) return;
    setForceLogoutLoading(true);
    try {
      await forceLogoutUser(confirmForceLogout.id);
      setConfirmForceLogout(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao forçar logout");
    } finally {
      setForceLogoutLoading(false);
    }
  }

  async function handleEditSave(data: { name: string; email: string; role: string }) {
    if (!editUser) return;
    setEditLoading(true);
    try {
      await updateUser(editUser.id, data);
      setEditUser(null);
      loadUsers();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao editar");
    } finally {
      setEditLoading(false);
    }
  }

  async function handleResetPassword(newPassword: string) {
    if (!resetUser) return;
    setResetLoading(true);
    try {
      await adminResetPassword(resetUser.id, newPassword);
      setResetUser(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao alterar senha");
    } finally {
      setResetLoading(false);
    }
  }

  async function handleBlock(user: User) {
    try {
      if (user.is_active) await blockUser(user.id);
      else await unblockUser(user.id);
      loadUsers();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-[#f8fafc]">Usuários</h1>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      <Card className="mb-6">
        <div className="flex flex-wrap gap-4">
          <input
            type="search"
            placeholder="Buscar..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] placeholder-[#64748b] focus:border-blue-500 focus:outline-none"
          />
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(0);
            }}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] focus:border-blue-500 focus:outline-none"
          >
            <option value="">Todos os papéis</option>
            <option value="super_admin">SuperAdmin</option>
            <option value="admin">Admin</option>
            <option value="compliance">Compliance</option>
            <option value="factory_manager">FactoryManager</option>
            <option value="viewer">Viewer</option>
          </select>
        </div>
      </Card>

      <Card>
        {loading ? (
          <p className="py-8 text-center text-[#94a3b8]">Carregando...</p>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Nome</TableHead>
                  <TableHead>Papel</TableHead>
                  <TableHead>Risco</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Criado em</TableHead>
                  <TableHead>Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="text-[#f8fafc]">{u.email}</TableCell>
                    <TableCell className="text-[#94a3b8]">{u.name}</TableCell>
                    <TableCell>
                      <Badge variant="info">{u.role}</Badge>
                    </TableCell>
                    <TableCell>
                      <span
                        className={
                          (u.risk_score ?? 0) >= 70
                            ? "text-red-400"
                            : (u.risk_score ?? 0) >= 40
                            ? "text-amber-400"
                            : "text-[#94a3b8]"
                        }
                      >
                        {(u as User & { risk_score?: number }).risk_score ?? 0}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={u.is_active ? "success" : "error"}>
                        {u.is_active ? "Ativo" : "Bloqueado"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-[#94a3b8]">
                      {new Date(u.created_at).toLocaleDateString("pt-BR")}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        <Button variant="secondary" size="sm" onClick={() => setEditUser(u)}>
                          Editar
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleBlock(u)}
                        >
                          {u.is_active ? "Bloquear" : "Desbloquear"}
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setResetUser({ id: u.id, email: u.email })}
                        >
                          Reset senha
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setConfirmForceLogout({ id: u.id, email: u.email })}
                        >
                          Forçar logout
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setLoginHistoryUser({ id: u.id, email: u.email })}
                        >
                          Histórico
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          className="text-red-400 hover:bg-red-900/30"
                          onClick={() => setConfirmDelete({ id: u.id, email: u.email })}
                        >
                          Excluir
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {users.length === 0 && (
              <p className="py-8 text-center text-[#94a3b8]">Nenhum usuário encontrado.</p>
            )}
            <div className="mt-4 flex justify-between">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={users.length < 50}
              >
                Próxima
              </Button>
            </div>
          </>
        )}
      </Card>

      <ConfirmDialog
        open={!!confirmDelete}
        title="Confirmar exclusão"
        message={
          confirmDelete
            ? `Tem certeza que deseja excluir o usuário ${confirmDelete.email}? Esta ação pode ser revertida posteriormente (soft delete).`
            : ""
        }
        confirmLabel="Excluir"
        variant="danger"
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmDelete(null)}
        loading={deleteLoading}
      />

      <ConfirmDialog
        open={!!confirmForceLogout}
        title="Forçar logout"
        message={
          confirmForceLogout
            ? `Invalidar todas as sessões do usuário ${confirmForceLogout.email}?`
            : ""
        }
        confirmLabel="Confirmar"
        variant="warning"
        onConfirm={handleConfirmForceLogout}
        onCancel={() => setConfirmForceLogout(null)}
        loading={forceLogoutLoading}
      />

      <UserEditModal
        open={!!editUser}
        user={editUser}
        onClose={() => setEditUser(null)}
        onSave={handleEditSave}
        loading={editLoading}
      />

      <ResetPasswordModal
        open={!!resetUser}
        user={resetUser}
        onClose={() => setResetUser(null)}
        onReset={handleResetPassword}
        loading={resetLoading}
      />

      <LoginHistoryDrawer
        open={!!loginHistoryUser}
        user={loginHistoryUser}
        onClose={() => setLoginHistoryUser(null)}
      />
    </div>
  );
}
