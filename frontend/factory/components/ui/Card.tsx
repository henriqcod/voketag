export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-graphite-200 bg-white shadow-theme-sm dark:border-graphite-800 dark:bg-graphite-900/50 dark:shadow-theme-md ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`border-b border-graphite-200 px-6 py-4 dark:border-graphite-800 ${className}`}>
      {children}
    </div>
  );
}

export function CardContent({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`p-6 ${className}`}>{children}</div>;
}
