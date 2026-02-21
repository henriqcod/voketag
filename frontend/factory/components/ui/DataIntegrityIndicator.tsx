"use client";

type Status = "verified" | "pending" | "degraded";

export function DataIntegrityIndicator({
  status = "verified",
  merkleRoot,
  blockchainTx,
}: {
  status?: Status;
  merkleRoot?: string;
  blockchainTx?: string;
}) {
  const config = {
    verified: {
      label: "Integridade verificada",
      color: "text-success",
      bg: "bg-success/10 dark:bg-success/20",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
    pending: {
      label: "Verificação pendente",
      color: "text-amber-600 dark:text-amber-400",
      bg: "bg-amber-500/10 dark:bg-amber-500/20",
      icon: (
        <svg className="h-5 w-5 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    degraded: {
      label: "Integridade degradada",
      color: "text-alert",
      bg: "bg-alert/10 dark:bg-alert/20",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
    },
  };

  const c = config[status];

  return (
    <div className={`inline-flex items-center gap-2 rounded-lg border border-graphite-200 px-3 py-2 ${c.bg} dark:border-graphite-700`}>
      <span className={c.color}>{c.icon}</span>
      <div>
        <p className={`text-sm font-medium ${c.color}`}>{c.label}</p>
        {merkleRoot && (
          <p className="truncate font-mono text-xs text-graphite-600 dark:text-graphite-400" title={merkleRoot}>
            {merkleRoot.slice(0, 16)}...
          </p>
        )}
      </div>
    </div>
  );
}
