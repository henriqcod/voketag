"use client";

import { useEffect, useRef, useCallback } from "react";
import { Html5Qrcode } from "html5-qrcode";

interface QRScannerProps {
  onScan: (code: string) => void;
  disabled?: boolean;
}

export function QRScanner({ onScan, disabled }: QRScannerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const handleScan = useCallback(
    (decodedText: string) => {
      if (decodedText?.trim() && !disabled) {
        onScan(decodedText.trim());
      }
    },
    [onScan, disabled]
  );

  useEffect(() => {
    if (!containerRef.current || disabled) return;

    const html5QrCode = new Html5Qrcode("qr-reader");
    const config = { fps: 5, qrbox: { width: 250, height: 250 } };

    html5QrCode
      .start(
        { facingMode: "environment" },
        config,
        (text: string) => handleScan(text),
        () => {}
      )
      .catch((err: Error) => {
        console.warn("QR scanner:", err.message);
      });

    return () => {
      html5QrCode.stop().catch(() => {});
    };
  }, [disabled, handleScan]);

  if (disabled) return null;

  return (
    <div ref={containerRef} className="qr-scanner-container">
      <div id="qr-reader" className="qr-reader" />
    </div>
  );
}
