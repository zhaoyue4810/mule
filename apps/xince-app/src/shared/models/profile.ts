export interface ProfileDimensionAggregate {
  dim_code: string;
  total_score: number;
}

export interface ProfilePersonaAggregate {
  persona_key?: string | null;
  persona_name?: string | null;
  count: number;
}

export interface ProfileReportHistoryItem {
  record_id: number;
  test_code: string;
  test_name: string;
  persona_key?: string | null;
  persona_name?: string | null;
  summary: string;
  total_score?: number | null;
  duration_seconds?: number | null;
  completed_at: string;
}

export interface AppProfileOverview {
  user_id: number;
  nickname: string;
  avatar_value: string;
  test_count: number;
  distinct_test_count: number;
  avg_duration_seconds: number;
  last_test_at?: string | null;
  dominant_dimensions: ProfileDimensionAggregate[];
  persona_distribution: ProfilePersonaAggregate[];
  recent_reports: ProfileReportHistoryItem[];
}
