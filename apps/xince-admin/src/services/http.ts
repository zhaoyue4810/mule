const API_BASE = import.meta.env.VITE_ADMIN_API_BASE_URL || "http://127.0.0.1:8080/api";
const TOKEN_KEY = "xc_admin_token";

function getToken() {
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

function redirectToLogin() {
  window.localStorage.removeItem(TOKEN_KEY);
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers || {});
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (response.status === 401) {
    redirectToLogin();
    throw new Error("登录已过期，请重新登录");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
