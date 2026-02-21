type Variant = "default" | "success" | "alert" | "warning" | "info";

const variants: Record<Variant, string> = {
  default: "bg-graphite-100 text-graphite-700 dark:bg-graphite-700 dark:text-graphite-200",
  success: "bg-success-100 text-success-600 dark:bg-success-500/20 dark:text-success-400",
  alert: "bg-error-100 text-error-600 dark:bg-error-500/20 dark:text-red-400",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400",
  info: "bg-primary-100 text-primary-700 dark:bg-primary-600/20 dark:text-primary-400",
};

export function Badge({
  children,
  variant = "default",
  className = "",
}: {
  children: React.ReactNode;
  variant?: Variant;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
