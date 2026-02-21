const DefaultIcon = (
  <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
  </svg>
);

export function EmptyState({
  title,
  description,
  icon,
  action,
}: {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}) {
  const displayIcon = icon ?? DefaultIcon;
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-graphite-300 bg-graphite-50 py-16 text-center dark:border-graphite-700 dark:bg-graphite-900/30">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-graphite-200 text-graphite-500 dark:bg-graphite-800 dark:text-graphite-400">
        {displayIcon}
      </div>
      <h3 className="text-lg font-medium text-graphite-800 dark:text-graphite-200">{title}</h3>
      {description && (
        <p className="mt-2 max-w-sm text-sm text-graphite-500 dark:text-graphite-400">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
