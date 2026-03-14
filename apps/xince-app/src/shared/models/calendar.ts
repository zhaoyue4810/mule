export interface CalendarEventItem {
  source: string;
  label: string;
  mood_level?: number | null;
  emoji?: string | null;
}

export interface CalendarDayDetail {
  date: string;
  activity_count: number;
  intensity: number;
  mood_level?: number | null;
  mood_emoji?: string | null;
  events: CalendarEventItem[];
}

export interface CalendarMonthPayload {
  year: number;
  month: number;
  items: CalendarDayDetail[];
}

export interface CalendarYearPayload {
  year: number;
  items: CalendarDayDetail[];
}

export interface CalendarStatsPayload {
  current_streak: number;
  active_days: number;
  average_mood: number;
  best_streak: number;
}
