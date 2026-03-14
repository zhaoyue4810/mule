import type {
  AuthSessionResponse,
  AuthUserPayload,
  PhoneSendCodeResponse,
} from "@/shared/models/auth";
import { request } from "@/shared/services/http";

const ACCESS_TOKEN_STORAGE_KEY = "xc_access_token";
const SESSION_USER_STORAGE_KEY = "xc_session_user";

function readStoredUser(): AuthUserPayload | null {
  const raw = uni.getStorageSync(SESSION_USER_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const value =
      typeof raw === "string" ? JSON.parse(raw) : (raw as AuthUserPayload);
    if (value && typeof value.user_id === "number") {
      return value;
    }
  } catch {
    return null;
  }

  return null;
}

export function getAccessToken() {
  const value = uni.getStorageSync(ACCESS_TOKEN_STORAGE_KEY);
  return typeof value === "string" && value ? value : "";
}

export function setAuthSession(session: AuthSessionResponse) {
  uni.setStorageSync(ACCESS_TOKEN_STORAGE_KEY, session.access_token);
  setSessionUser(session.user);
}

export function getSessionUser() {
  return readStoredUser();
}

export function setSessionUser(user: AuthUserPayload) {
  uni.setStorageSync(SESSION_USER_STORAGE_KEY, JSON.stringify(user));
}

export function clearAuthSession() {
  uni.removeStorageSync(ACCESS_TOKEN_STORAGE_KEY);
  uni.removeStorageSync(SESSION_USER_STORAGE_KEY);
}

export async function guestLogin(nickname = "心测访客") {
  const session = await request<AuthSessionResponse>("/auth/guest", "POST", {
    nickname,
  });
  setAuthSession(session);
  return session;
}

export async function loginWithWechatMiniProgram(
  nickname = "微信用户",
  avatarValue = "🧠",
) {
  const code = await getWechatLoginCode();
  const session = await request<AuthSessionResponse>(
    "/auth/wechat/mini-program",
    "POST",
    {
      code,
      nickname,
      avatar_value: avatarValue,
    },
  );
  setAuthSession(session);
  return session;
}

export async function fetchAuthMe() {
  return request<AuthUserPayload>("/auth/me");
}

export async function sendPhoneCode(phone: string) {
  return request<PhoneSendCodeResponse>("/auth/phone/send-code", "POST", {
    phone,
  });
}

export async function bindPhone(phone: string, code: string) {
  const session = await request<AuthSessionResponse>("/auth/phone/bind", "POST", {
    phone,
    code,
  });
  setAuthSession(session);
  return session;
}

export async function loginWithPhone(phone: string, code: string) {
  const session = await request<AuthSessionResponse>("/auth/phone-login", "POST", {
    phone,
    code,
  });
  setAuthSession(session);
  return session;
}

export async function ensureGuestSession() {
  const token = getAccessToken();
  if (token) {
    try {
      const user = await fetchAuthMe();
      uni.setStorageSync(SESSION_USER_STORAGE_KEY, JSON.stringify(user));
      return user;
    } catch {
      clearAuthSession();
    }
  }

  const session = await guestLogin();
  return session.user;
}

export async function ensureAppSession() {
  const token = getAccessToken();
  if (token) {
    try {
      const user = await fetchAuthMe();
      uni.setStorageSync(SESSION_USER_STORAGE_KEY, JSON.stringify(user));
      return user;
    } catch {
      clearAuthSession();
    }
  }

  // #ifdef MP-WEIXIN
  try {
    const session = await loginWithWechatMiniProgram();
    return session.user;
  } catch (error) {
    console.warn("WeChat mini program login failed, fallback to guest session", error);
  }
  // #endif

  const session = await guestLogin();
  return session.user;
}

async function getWechatLoginCode() {
  return new Promise<string>((resolve, reject) => {
    uni.login({
      provider: "weixin",
      success: (result) => {
        if (result.code) {
          resolve(result.code);
          return;
        }
        reject(new Error("WeChat login did not return code"));
      },
      fail: (error) => {
        reject(
          new Error(
            typeof error?.errMsg === "string" && error.errMsg
              ? error.errMsg
              : "WeChat login failed",
          ),
        );
      },
    });
  });
}
