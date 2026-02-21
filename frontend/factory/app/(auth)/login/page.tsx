"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";

type FormValues = {
  email: string;
  password: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>();

  const onSubmit = async (data: FormValues) => {
    setError(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081"}/auth/login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Falha no login");
      }
      const json = await res.json();
      if (typeof window !== "undefined" && json.access_token) {
        const { setAuthCookies } = await import("@/lib/auth-cookies");
        setAuthCookies(json.access_token, json.role);
      }
      const redirect = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("redirect") : null;
      router.push(redirect && redirect.startsWith("/") ? redirect : "/dashboard");
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div className="rounded-xl border border-graphite-800 bg-graphite-900 p-8 shadow-lg">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-white">VokeTag Factory</h1>
        <p className="mt-2 text-sm text-graphite-400">
          Portal da Fábrica — Acesso seguro
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-graphite-300">
            E-mail
          </label>
          <input
            type="email"
            {...register("email", { required: "Obrigatório" })}
            className="mt-1 w-full rounded-lg border border-graphite-700 bg-graphite-950 px-4 py-2.5 text-white placeholder-graphite-500"
            placeholder="seu@email.com"
          />
          {errors.email && (
            <p className="mt-1 text-sm text-alert">{errors.email.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-graphite-300">
            Senha
          </label>
          <input
            type="password"
            {...register("password", { required: "Obrigatório" })}
            className="mt-1 w-full rounded-lg border border-graphite-700 bg-graphite-950 px-4 py-2.5 text-white placeholder-graphite-500"
          />
          {errors.password && (
            <p className="mt-1 text-sm text-alert">{errors.password.message}</p>
          )}
        </div>
        {error && (
          <div className="rounded-lg border border-alert/30 bg-alert/10 p-3 text-sm text-alert">
            {error}
          </div>
        )}
        <button
          type="submit"
          className="w-full rounded-lg bg-primary-600 py-2.5 text-sm font-medium text-white hover:bg-primary-500"
        >
          Entrar
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-graphite-500">
        Em desenvolvimento: o backend pode não ter endpoint de login. Use token
        manual em localStorage se necessário.
      </p>
    </div>
  );
}
