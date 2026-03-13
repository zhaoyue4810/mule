export interface AuthUserPayload {
  user_id: number;
  nickname: string;
  avatar_value: string;
  is_guest: boolean;
  has_openid: boolean;
  has_phone: boolean;
  masked_phone?: string | null;
}

export interface AuthSessionResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: AuthUserPayload;
}

export interface PhoneSendCodeResponse {
  phone: string;
  expires_in_seconds: number;
  provider: string;
  debug_code?: string | null;
}
