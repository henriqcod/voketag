"use client";

import { useState, useCallback, useMemo } from "react";

/** Lat/lng heat point (pre-aggregated server-side for 1M+ scans) */
export type GeoHeatPoint = { lat: number; lng: number; count: number };

/** Country code to approximate centroid for fallback */
const COUNTRY_CENTROIDS: Record<string, [number, number]> = {
  BR: [-14.2, -51.9],
  PT: [39.4, -8.2],
  AR: [-34.6, -58.4],
  MX: [19.4, -99.1],
  CO: [4.6, -74.1],
  CL: [-33.4, -70.7],
  US: [37.1, -95.7],
  ES: [40.4, -3.7],
  FR: [46.2, 2.2],
  DE: [51.2, 10.5],
  GB: [55.4, -3.4],
  IT: [41.9, 12.6],
};

function latLngToXY(lat: number, lng: number, w: number, h: number) {
  const x = ((lng + 180) / 360) * w;
  const y = ((90 - lat) / 180) * h;
  return { x, y };
}

type Period = "1d" | "7d" | "30d";

interface GeoHeatMapProps {
  points?: GeoHeatPoint[];
  countryData?: { country: string; count: number }[];
  period?: Period;
  onPeriodChange?: (p: Period) => void;
  isLoading?: boolean;
}

export function GeoHeatMap({
  points: rawPoints = [],
  countryData = [],
  period = "1d",
  onPeriodChange,
  isLoading,
}: GeoHeatMapProps) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const points = useMemo(() => {
    if (rawPoints.length > 0) return rawPoints;
    return countryData.map((g) => {
      const c = COUNTRY_CENTROIDS[g.country] ?? [0, 0];
      return { lat: c[0], lng: c[1], count: g.count };
    });
  }, [rawPoints, countryData]);

  const maxCount = useMemo(
    () => (points.length ? Math.max(...points.map((p) => p.count), 1) : 1),
    [points]
  );

  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -0.15 : 0.15;
      setZoom((z) => Math.max(0.5, Math.min(3, z + delta)));
    },
    []
  );

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  }, [pan]);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging) return;
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    },
    [isDragging, dragStart]
  );

  const handleMouseUp = useCallback(() => setIsDragging(false), []);
  const handleMouseLeave = useCallback(() => setIsDragging(false), []);

  const W = 360;
  const H = 180;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg bg-graphite-100 dark:bg-graphite-900">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-2 rounded-lg bg-graphite-50 dark:bg-graphite-900/50">
        <p className="text-sm text-graphite-500">Nenhum scan no período</p>
        {onPeriodChange && (
          <div className="flex gap-1">
            {(["1d", "7d", "30d"] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => onPeriodChange(p)}
                className={`rounded px-2 py-1 text-xs font-medium ${
                  period === p
                    ? "bg-primary-600 text-white"
                    : "bg-graphite-200 text-graphite-600 hover:bg-graphite-300 dark:bg-graphite-700 dark:text-graphite-300"
                }`}
              >
                {p === "1d" ? "24h" : p === "7d" ? "7 dias" : "30 dias"}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        {onPeriodChange && (
          <div className="flex gap-1">
            {(["1d", "7d", "30d"] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => onPeriodChange(p)}
                className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
                  period === p
                    ? "bg-primary-600 text-white dark:bg-primary-500"
                    : "bg-graphite-200 text-graphite-600 hover:bg-graphite-300 dark:bg-graphite-700 dark:text-graphite-300 dark:hover:bg-graphite-600"
                }`}
              >
                {p === "1d" ? "24h" : p === "7d" ? "7 dias" : "30 dias"}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(3, z + 0.25))}
            className="flex h-7 w-7 items-center justify-center rounded bg-graphite-200 text-graphite-700 hover:bg-graphite-300 dark:bg-graphite-700 dark:text-graphite-300 dark:hover:bg-graphite-600"
            aria-label="Zoom in"
          >
            +
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}
            className="flex h-7 w-7 items-center justify-center rounded bg-graphite-200 text-graphite-700 hover:bg-graphite-300 dark:bg-graphite-700 dark:text-graphite-300 dark:hover:bg-graphite-600"
            aria-label="Zoom out"
          >
            −
          </button>
        </div>
      </div>
      <div
        className="relative h-64 w-full overflow-hidden rounded-lg border border-graphite-200 bg-graphite-100 dark:border-graphite-700 dark:bg-graphite-900/50"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
      >
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="absolute inset-0 h-full w-full"
          preserveAspectRatio="xMidYMid slice"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "center center",
          }}
        >
          <defs>
            <linearGradient id="heatGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#2563eb" stopOpacity="0.4" />
            </linearGradient>
          </defs>
          {/* Light grid for map context */}
          {Array.from({ length: 12 }, (_, i) => (
            <line
              key={`v${i}`}
              x1={(i + 1) * 30}
              y1={0}
              x2={(i + 1) * 30}
              y2={H}
              stroke="currentColor"
              strokeWidth="0.3"
              className="text-graphite-200 dark:text-graphite-800"
            />
          ))}
          {Array.from({ length: 6 }, (_, i) => (
            <line
              key={`h${i}`}
              x1={0}
              y1={(i + 1) * 30}
              x2={W}
              y2={(i + 1) * 30}
              stroke="currentColor"
              strokeWidth="0.3"
              className="text-graphite-200 dark:text-graphite-800"
            />
          ))}
          {points.map((p, i) => {
            const { x, y } = latLngToXY(p.lat, p.lng, W, H);
            const r = Math.max(2, Math.min(12, 3 + (p.count / maxCount) * 10));
            const opacity = Math.max(0.3, 0.4 + (p.count / maxCount) * 0.5);
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r={r}
                fill="url(#heatGrad)"
                fillOpacity={opacity}
                className="transition-opacity hover:opacity-90"
              >
                <title>{`${p.lat.toFixed(1)}°, ${p.lng.toFixed(1)}°: ${p.count.toLocaleString()} scans`}</title>
              </circle>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
