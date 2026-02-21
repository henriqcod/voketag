/**
 * Geolocalização opcional para backend antifraude
 * Solicita permissão ao usuário - não bloqueia se recusar
 */

export interface GeoCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

const GEO_TIMEOUT = 5000;

export async function getGeolocation(): Promise<GeoCoordinates | null> {
  if (typeof window === "undefined" || !navigator.geolocation) return null;
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        }),
      () => resolve(null),
      { timeout: GEO_TIMEOUT, enableHighAccuracy: false, maximumAge: 60000 }
    );
  });
}
