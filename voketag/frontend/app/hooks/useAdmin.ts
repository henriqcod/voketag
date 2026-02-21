"use client";

import { useState, useEffect } from "react";
import { adminAPI } from "@/lib/api-client";

interface DashboardStats {
  users: number;
  products: number;
  scans: number;
  timestamp?: string;
}

interface User {
  id?: string;
  name: string;
  email: string;
  role?: string;
}

export function useAdminDashboard() {
  const [stats, setStats] = useState<DashboardStats>({ users: 0, products: 0, scans: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminAPI.getDashboard();
      setStats(data.stats || { users: 0, products: 0, scans: 0 });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  return {
    stats,
    loading,
    error,
    fetchDashboard,
  };
}

export function useAdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminAPI.getUsers();
      setUsers(data.users || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar usuários");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return {
    users,
    loading,
    error,
    fetchUsers,
  };
}