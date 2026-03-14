export interface ProfileDimensionAggregate {
  dim_code: string;
  total_score: number;
}

export interface ProfilePersonaAggregate {
  persona_key?: string | null;
  persona_name?: string | null;
  count: number;
}

export interface ProfileBadgeItem {
  badge_key: string;
  name: string;
  emoji: string;
  tier: number;
  unlock_count: number;
  unlocked_at: string;
}

export interface ProfileCalendarHeatmapItem {
  date: string;
  activity_count: number;
  intensity: number;
}

export interface ProfileSoulFragmentItem {
  fragment_key: string;
  name: string;
  emoji?: string | null;
  category: string;
  insight?: string | null;
  unlocked_at: string;
}

export interface ProfileSoulFragmentCategoryProgress {
  category_code: string;
  category_name: string;
  unlocked_count: number;
  total_count: number;
  completed: boolean;
  complete_insight?: string | null;
}

export interface ProfileSoulFragmentMapItem {
  fragment_key: string;
  name: string;
  emoji?: string | null;
  category: string;
  insight?: string | null;
  collected: boolean;
  unlocked_at?: string | null;
}

export interface DailyQuestionStatePayload {
  question_id: number;
  question_text: string;
  options: string[];
  answer_date: string;
  answered: boolean;
  selected_index?: number | null;
  insight?: string | null;
  current_streak: number;
  best_streak: number;
  recent_answered_days: number;
  retroactive_dates: string[];
  unlocked_badges: Array<{
    badge_key: string;
    name: string;
    emoji: string;
  }>;
}

export interface ProfileSettingsPayload {
  sound_enabled: boolean;
}

export interface OnboardingProfilePayload {
  nickname: string;
  avatar_value: string;
  bio: string;
  gender: number;
  birth_year?: number | null;
  birth_month?: number | null;
  onboarding_completed: boolean;
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
  badges: ProfileBadgeItem[];
  calendar_heatmap: ProfileCalendarHeatmapItem[];
  soul_fragments: ProfileSoulFragmentItem[];
  fragment_progress: ProfileSoulFragmentCategoryProgress[];
  fragment_map: ProfileSoulFragmentMapItem[];
  recent_reports: ProfileReportHistoryItem[];
}
