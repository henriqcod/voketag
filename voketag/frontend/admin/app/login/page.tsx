"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login } from "@/lib/api-client";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [expiredMsg, setExpiredMsg] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (searchParams.get("expired") === "1") setExpiredMsg(true);
  }, [searchParams]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(email, password);
      localStorage.setItem("admin_token", res.access_token);
      localStorage.setItem("admin_refresh_token", res.refresh_token);
      const maxAge = res.expires_in ?? 3600;
      document.cookie = `admin_token=${encodeURIComponent(res.access_token)}; path=/; max-age=${maxAge}; SameSite=Lax`;
      router.push("/dashboard");
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login falhou");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0f172a] px-4">
      <div className="w-full max-w-md">
        <div className="rounded-xl border border-[#334155] bg-[#1e293b] p-8 shadow-xl">
          <h1 className="mb-2 text-2xl font-bold text-[#f8fafc]">
            VokeTag Admin
          </h1>
          <p className="mb-6 text-sm text-[#94a3b8]">
            GOD MODE — Área restrita
          </p>
          {expiredMsg && (
            <p className="mb-4 rounded-lg border border-amber-800 bg-amber-900/30 px-4 py-2 text-sm text-amber-300">
              Sessão expirada. Faça login novamente.
            </p>
          )}
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-[#94a3b8]"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-lg border border-[#334155] bg-[#0f172a] px-4 py-3 text-[#f8fafc] placeholder-[#64748b] focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="admin@voketag.com"
              />
            </div>
            <div className="mb-6">
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-medium text-[#94a3b8]"
              >
                Senha
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-lg border border-[#334155] bg-[#0f172a] px-4 py-3 text-[#f8fafc] placeholder-[#64748b] focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            {error && (
              <p className="mb-4 rounded-lg border border-red-800 bg-red-900/30 px-4 py-2 text-sm text-red-300">
                {error}
              </p>
            )}
            {process.env.NODE_ENV === "development" && (
              <p className="mb-4 rounded border border-[#334155] bg-[#0f172a]/50 px-4 py-2 text-xs text-[#94a3b8]">
                Primeiro acesso? Crie um admin:{" "}
                <code className="text-[#64748b]">
                  cd services/admin-service && python scripts/create_admin.py
                  admin@voketag.com SuaSenha123 &quot;Admin&quot;
                </code>
              </p>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-[#1e293b] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Entrando..." : "Entrar"}
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-[#0f172a] text-[#94a3b8]">Carregando...</div>}>
      <LoginForm />
    </Suspense>
  );
}
