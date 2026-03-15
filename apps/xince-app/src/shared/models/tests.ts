export interface PublishedTestSummary {
  test_code: string;
  name: string;
  category: string;
  description?: string | null;
  is_match_enabled: boolean;
  participant_count: number;
  version: number;
  question_count: number;
  duration_hint?: string | null;
  cover_gradient?: string | null;
}

export interface PublishedDimensionSummary {
  dim_code: string;
  dim_name: string;
  max_score: number;
  sort_order: number;
}

export interface PublishedPersonaSummary {
  persona_key: string;
  persona_name: string;
  emoji?: string | null;
  rarity_percent?: number | null;
  description?: string | null;
  keywords: string[];
}

export interface PublishedTestDetail {
  test_code: string;
  name: string;
  category: string;
  is_match_enabled: boolean;
  participant_count: number;
  sort_order: number;
  version: number;
  question_count: number;
  dimension_count: number;
  persona_count: number;
  duration_hint?: string | null;
  description?: string | null;
  cover_gradient?: string | null;
  report_template_code?: string | null;
  dimensions: PublishedDimensionSummary[];
  personas: PublishedPersonaSummary[];
}

export interface PublishedOptionPayload {
  option_code?: string | null;
  seq: number;
  label: string;
  emoji?: string | null;
  value: number;
}

export interface PublishedQuestionPayload {
  question_code?: string | null;
  seq: number;
  question_text: string;
  interaction_type: string;
  emoji?: string | null;
  config?: Record<string, unknown> | null;
  dim_weights: Record<string, unknown>;
  options: PublishedOptionPayload[];
}

export interface PublishedTestQuestionnaire {
  test_code: string;
  name: string;
  category: string;
  version: number;
  duration_hint?: string | null;
  question_count: number;
  questions: PublishedQuestionPayload[];
}

export interface TestSubmitAnswerPayload {
  question_seq: number;
  option_code?: string | null;
  numeric_value?: number | null;
  ordered_option_codes?: string[] | null;
  point?: { x: number; y: number } | null;
}

export interface TestSubmitRequest {
  user_id?: number | null;
  nickname?: string | null;
  duration_seconds?: number | null;
  answers: TestSubmitAnswerPayload[];
}

export interface SubmittedAnswerSummary {
  question_seq: number;
  option_code?: string | null;
  label: string;
}

export interface UnlockedBadgeSummary {
  badge_key: string;
  name: string;
  emoji: string;
  tier: number;
}

export interface UnlockedSoulFragmentSummary {
  fragment_key: string;
  name: string;
  emoji?: string | null;
  category: string;
  insight?: string | null;
}

export interface TestSubmitResponse {
  record_id: number;
  user_id: number;
  test_code: string;
  version: number;
  total_score: number;
  dimension_scores: Record<string, number>;
  persona_key?: string | null;
  persona_name?: string | null;
  report_summary: string;
  answers: SubmittedAnswerSummary[];
  unlocked_badges: UnlockedBadgeSummary[];
  unlocked_fragments: UnlockedSoulFragmentSummary[];
}
