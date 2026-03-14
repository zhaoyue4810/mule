import type {
  MatchCreateResponse,
  MatchHistoryResponse,
  MatchInviteDetail,
  MatchJoinResponse,
  MatchResultPayload,
} from "@/shared/models/match";
import { request } from "@/shared/services/http";

export async function createMatchInvite(testCode: string) {
  return request<MatchCreateResponse>("/match/create", "POST", {
    test_code: testCode,
  });
}

export async function fetchMatchInviteDetail(code: string) {
  return request<MatchInviteDetail>(`/match/invite/${encodeURIComponent(code)}`);
}

export async function joinMatchInvite(code: string) {
  return request<MatchJoinResponse>(`/match/join/${encodeURIComponent(code)}`, "POST");
}

export async function fetchMatchResult(sessionId: number) {
  return request<MatchResultPayload>(`/match/result/${sessionId}`);
}

export async function fetchMatchHistory() {
  return request<MatchHistoryResponse>("/match/history");
}
