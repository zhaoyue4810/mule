const API_BASE = import.meta.env.VITE_ADMIN_API_BASE_URL || "http://127.0.0.1:8080/api";

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
