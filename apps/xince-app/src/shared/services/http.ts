type RequestMethod = "GET" | "POST" | "PUT" | "DELETE";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8080/api/app";

const ACCESS_TOKEN_STORAGE_KEY = "xc_access_token";

export async function request<T>(
  path: string,
  method: RequestMethod = "GET",
  data?: string | Record<string, unknown> | ArrayBuffer,
): Promise<T> {
  const response = await uni.request({
    url: `${API_BASE_URL}${path}`,
    method,
    data,
    timeout: 10000,
    header: buildHeaders(),
  });

  const statusCode = response.statusCode ?? 500;
  if (statusCode >= 400) {
    const message =
      typeof response.data === "object" && response.data && "detail" in response.data
        ? String((response.data as { detail: string }).detail)
        : `Request failed with status ${statusCode}`;
    throw new Error(message);
  }

  return response.data as T;
}

function buildHeaders() {
  const token = uni.getStorageSync(ACCESS_TOKEN_STORAGE_KEY);
  if (typeof token === "string" && token) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }
  return {};
}
