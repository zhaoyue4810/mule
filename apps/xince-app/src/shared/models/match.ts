export interface MatchUserSummary {
  user_id: number;
  nickname: string;
  avatar_value: string;
}

export interface MatchBadgeSummary {
  badge_key: string;
  name: string;
  emoji: string;
  unlocked_at: string;
}

export interface MatchSessionSummary {
  session_id: number;
  test_code: string;
  test_name: string;
  status: string;
  invite_code: string;
  invite_link?: string | null;
  compatibility_score?: number | null;
  created_at: string;
  completed_at?: string | null;
}

export interface MatchCreateResponse extends MatchSessionSummary {
  initiator: MatchUserSummary;
  share_message: string;
}

export interface MatchInviteDetail extends MatchSessionSummary {
  initiator: MatchUserSummary;
  partner?: MatchUserSummary | null;
  partner_joined: boolean;
  requires_test_completion: boolean;
  can_join: boolean;
}

export interface MatchJoinResponse {
  session_id: number;
  status: string;
  result_ready: boolean;
  compatibility_score?: number | null;
  unlocked_badges: MatchBadgeSummary[];
}

export interface MatchDimensionComparisonItem {
  dim_code: string;
  initiator_score: number;
  partner_score: number;
  difference: number;
  similarity: number;
  relation: string;
}

export interface MatchResultPayload {
  session_id: number;
  status: string;
  test_code: string;
  test_name: string;
  compatibility_score: number;
  tier: string;
  analysis: string;
  created_at: string;
  completed_at?: string | null;
  initiator: MatchUserSummary;
  partner: MatchUserSummary;
  dimension_comparison: MatchDimensionComparisonItem[];
  similar_dimensions: string[];
  complementary_dimensions: string[];
  unlocked_badges: MatchBadgeSummary[];
}

export interface MatchHistoryItem {
  session_id: number;
  test_code: string;
  test_name: string;
  status: string;
  partner?: MatchUserSummary | null;
  compatibility_score?: number | null;
  tier?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface MatchHistoryResponse {
  items: MatchHistoryItem[];
  duo_badges: MatchBadgeSummary[];
}
