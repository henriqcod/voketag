"use client";

import { useEffect, useRef } from "react";

interface NFCReaderProps {
  onScan: (payload: string) => void;
  disabled?: boolean;
}

export function NFCReader({ onScan, disabled }: NFCReaderProps) {
  const mounted = useRef(true);

  useEffect(() => {
    if (disabled || typeof window === "undefined" || !("NDEFReader" in window)) return;

    const NDEFReaderClass = (window as unknown as { NDEFReader: new () => { scan: (o?: { signal?: AbortSignal }) => Promise<void>; addEventListener: (t: string, h: (e: { message: { records: { recordType: string; data?: BufferSource }[] } }) => void) => void } }).NDEFReader;
    const reader = new NDEFReaderClass();
    const controller = new AbortController();

    const handleReading = (e: { message: { records: { recordType: string; data?: BufferSource }[] } }) => {
      if (!mounted.current) return;
      try {
        for (const record of e.message.records) {
          if (record.recordType === "url" && record.data) {
            const dec = new TextDecoder();
            const url = dec.decode(record.data);
            if (url) onScan(url);
          } else if (record.data) {
            const dec = new TextDecoder();
            onScan(dec.decode(record.data));
          }
        }
      } catch {}
    };

    reader.addEventListener("reading", handleReading);
    reader.scan({ signal: controller.signal }).catch(() => {});

    return () => {
      mounted.current = false;
      controller.abort();
    };
  }, [onScan, disabled]);

  return null;
}
