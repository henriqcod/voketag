export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-graphite-800 ${className}`}
      aria-hidden
    />
  );
}
