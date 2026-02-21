"use client";

import { useForm } from "react-hook-form";
import { useSettings, useSaveSettings } from "@/hooks/useSettings";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

type FormValues = {
  verification_url: string;
  ntag_default: "213" | "215" | "216";
  webhook_url: string;
  antifraud_scan_threshold: number;
  sandbox_mode: boolean;
};

export default function SettingsPage() {
  const { data: settings, isLoading } = useSettings();
  const saveMutation = useSaveSettings();

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    values: settings
      ? {
          verification_url: settings.verification_url,
          ntag_default: settings.ntag_default,
          webhook_url: settings.webhook_url ?? "",
          antifraud_scan_threshold: settings.antifraud_scan_threshold,
          sandbox_mode: settings.sandbox_mode,
        }
      : undefined,
  });

  const onSubmit = (data: FormValues) => {
    saveMutation.mutate({
      verification_url: data.verification_url,
      ntag_default: data.ntag_default,
      webhook_url: data.webhook_url || undefined,
      antifraud_scan_threshold: data.antifraud_scan_threshold,
      sandbox_mode: data.sandbox_mode,
    });
  };

  if (isLoading || !settings) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-semibold text-graphite-900 dark:text-white">Configurações</h2>
        <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
          Configurar Portal da Fábrica
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">URL de Verificação</h3>
            <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
              URL base usada nos QR Codes e links de verificação
            </p>
          </CardHeader>
          <CardContent>
            <input
              type="url"
              {...register("verification_url", { required: true })}
              className="w-full max-w-md rounded-lg border border-graphite-300 bg-white px-4 py-2 text-graphite-900 placeholder-graphite-400 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white dark:placeholder-graphite-500"
              placeholder="https://verify.voketag.com.br"
            />
            {errors.verification_url && (
              <p className="mt-1 text-sm text-alert">Campo obrigatório</p>
            )}
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Padrão NTAG</h3>
            <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
              Modelo de tag NFC para exportação
            </p>
          </CardHeader>
          <CardContent>
            <select
              {...register("ntag_default")}
              className="w-full max-w-md rounded-lg border border-graphite-300 bg-white px-4 py-2 text-graphite-900 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
            >
              <option value="213">NTAG213</option>
              <option value="215">NTAG215</option>
              <option value="216">NTAG216</option>
            </select>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Webhook de notificação</h3>
            <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
              URL para receber notificações de eventos
            </p>
          </CardHeader>
          <CardContent>
            <input
              type="url"
              {...register("webhook_url")}
              className="w-full max-w-md rounded-lg border border-graphite-300 bg-white px-4 py-2 text-graphite-900 placeholder-graphite-400 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white dark:placeholder-graphite-500"
              placeholder="https://..."
            />
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Modo Sandbox / Produção</h3>
            <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
              Sandbox para testes; Produção para ambiente real
            </p>
          </CardHeader>
          <CardContent>
            <label className="flex cursor-pointer items-center gap-2">
              <input type="checkbox" {...register("sandbox_mode")} className="rounded" />
              <span className="text-sm text-graphite-700 dark:text-graphite-300">Modo sandbox (testes)</span>
            </label>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Antifraude</h3>
            <p className="mt-1 text-sm text-graphite-400">
              Limite de scans para detecção de risco
            </p>
          </CardHeader>
          <CardContent>
            <input
              type="number"
              min={1}
              max={100}
              {...register("antifraud_scan_threshold", {
                valueAsNumber: true,
                min: 1,
                max: 100,
              })}
              className="w-full max-w-[200px] rounded-lg border border-graphite-300 bg-white px-4 py-2 text-graphite-900 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
            />
          </CardContent>
        </Card>

        <div className="mt-6">
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="rounded-lg bg-primary-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-primary-500 disabled:opacity-50"
          >
            {saveMutation.isPending ? "Salvando..." : "Salvar configurações"}
          </button>
        </div>
      </form>
    </div>
  );
}
