export interface ReportDimensionHighlight {
  dim_code: string;
  score: number;
}

export interface ReportRadarDimension {
  dim_code: string;
  label: string;
  score: number;
  normalized_score: number;
}

export interface ReportPersonaTag {
  label: string;
  tone: string;
}

export interface ReportSoulWeather {
  title: string;
  mood: string;
  description: string;
}

export interface ReportMetaphorCard {
  category: string;
  title: string;
  subtitle: string;
  emoji: string;
}

export interface ReportDNAItem {
  dim_code: string;
  label: string;
  percentage: number;
}

export interface ReportActionGuide {
  title: string;
  description: string;
}

export interface ReportShareCard {
  theme: string;
  background: string;
  title: string;
  subtitle: string;
  accent: string;
  badge: string;
  footer: string;
  stat_chips: string[];
  highlight_lines: string[];
  share_text: string;
}

export interface ReportAiStatusPayload {
  record_id: number;
  status: string;
  provider?: string | null;
  model_used?: string | null;
  content?: string | null;
  updated: boolean;
}

export interface ReportPersonaPayload {
  persona_key?: string | null;
  persona_name?: string | null;
  description?: string | null;
  keywords: string[];
}

export interface AppReportDetail {
  record_id: number;
  test_code: string;
  test_name: string;
  version: number;
  total_score?: number | null;
  summary: string;
  dimension_scores: Record<string, number>;
  top_dimensions: ReportDimensionHighlight[];
  radar_dimensions: ReportRadarDimension[];
  persona_tags: ReportPersonaTag[];
  soul_weather: ReportSoulWeather;
  metaphor_cards: ReportMetaphorCard[];
  dna_segments: ReportDNAItem[];
  action_guides: ReportActionGuide[];
  result_tier: string;
  persona: ReportPersonaPayload;
  answered_count: number;
  duration_seconds?: number | null;
  ai_status: string;
  ai_text?: string | null;
  share_card_url?: string | null;
  share_card: ReportShareCard;
}
