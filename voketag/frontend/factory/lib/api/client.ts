const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/v1";

type RequestInitWithAuth = RequestInit & {
  token?: string | null;
};

async function getAuthHeaders(): Promise<HeadersInit> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("voketag_token")
      : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInitWithAuth = {}
): Promise<T> {
  const { token, ...init } = options;
  const headers = await getAuthHeaders();
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  const res = await fetch(url, {
    ...init,
    headers: {
      ...headers,
      ...(init.headers as Record<string, string>),
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}
