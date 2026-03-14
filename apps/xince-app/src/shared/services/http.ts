type RequestMethod = "GET" | "POST" | "PUT" | "DELETE";
type RequestOptions = {
  retryCount?: number;
  skipAuthRetry?: boolean;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8080/api/app";

const ACCESS_TOKEN_STORAGE_KEY = "xc_access_token";

export async function request<T>(
  path: string,
  method: RequestMethod = "GET",
  data?: string | Record<string, unknown> | ArrayBuffer,
  options: RequestOptions = {},
): Promise<T> {
  let response: UniApp.RequestSuccessCallbackResult;
  try {
    response = await uni.request({
      url: `${API_BASE_URL}${path}`,
      method,
      data,
      timeout: 10000,
      header: buildHeaders(),
    });
  } catch (err) {
    const message = formatRequestError(err);
    if ((options.retryCount || 0) < 1 && isRetryableNetworkError(message)) {
      return request<T>(path, method, data, {
        ...options,
        retryCount: (options.retryCount || 0) + 1,
      });
    }
    throw new Error(message);
  }

  const statusCode = response.statusCode ?? 500;
  if (statusCode === 401) {
    const isAuthPath = path.startsWith("/auth/");
    if (!isAuthPath && !options.skipAuthRetry && (options.retryCount || 0) < 1) {
      const refreshed = await refreshSessionToken();
      if (refreshed) {
        return request<T>(path, method, data, {
          ...options,
          retryCount: (options.retryCount || 0) + 1,
        });
      }
    }
    throw new Error("登录状态已过期，请重试");
  }

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

function isRetryableNetworkError(message: string) {
  return (
    message.includes("timeout") ||
    message.includes("超时") ||
    message.includes("network") ||
    message.includes("网络")
  );
}

function formatRequestError(err: unknown) {
  const raw =
    typeof err === "string"
      ? err
      : typeof err === "object" && err && "errMsg" in err
        ? String((err as { errMsg?: string }).errMsg || "")
        : err instanceof Error
          ? err.message
          : "";

  if (raw.includes("timeout") || raw.includes("超时")) {
    return "网络超时，请稍后重试";
  }
  if (raw.includes("network") || raw.includes("fail")) {
    return "网络异常，请检查连接后重试";
  }
  return raw || "请求失败，请稍后重试";
}

let refreshingPromise: Promise<boolean> | null = null;

async function refreshSessionToken() {
  if (refreshingPromise) {
    return refreshingPromise;
  }
  refreshingPromise = (async () => {
    try {
      const authModule = await import("@/shared/services/auth");
      await authModule.ensureAppSession();
      return true;
    } catch {
      return false;
    } finally {
      refreshingPromise = null;
    }
  })();
  return refreshingPromise;
}
