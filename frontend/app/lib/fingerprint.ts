/**
 * Fingerprint básico do dispositivo para antifraude
 * Usa dados disponíveis sem bibliotecas externas
 */

function simpleHash(str: string): string {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    const c = str.charCodeAt(i);
    h = (h << 5) - h + c;
    h = h & h;
  }
  return Math.abs(h).toString(36);
}

export function getDeviceFingerprint(): string {
  if (typeof window === "undefined") return "";
  const parts = [
    navigator.userAgent,
    navigator.language,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    window.screen.width + "x" + window.screen.height,
    String(window.screen.colorDepth),
    String(navigator.hardwareConcurrency || 0),
    String((navigator as Navigator & { deviceMemory?: number }).deviceMemory || 0),
    String(navigator.platform),
    String(window.devicePixelRatio || 1),
  ];
  return simpleHash(parts.join("|"));
}
