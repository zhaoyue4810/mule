import type {
  CalendarMonthPayload,
  CalendarStatsPayload,
  CalendarYearPayload,
} from "@/shared/models/calendar";
import { request } from "@/shared/services/http";

export function fetchCalendarMonth(year: number, month: number) {
  return request<CalendarMonthPayload>(`/calendar/month?year=${year}&month=${month}`);
}

export function fetchCalendarYear(year: number) {
  return request<CalendarYearPayload>(`/calendar/year?year=${year}`);
}

export function fetchCalendarStats(year?: number) {
  return request<CalendarStatsPayload>(
    year ? `/calendar/stats?year=${year}` : "/calendar/stats",
  );
}

export function recordCalendarMood(moodLevel: number, recordDate?: string) {
  return request<CalendarStatsPayload>("/calendar/mood", "POST", {
    mood_level: moodLevel,
    record_date: recordDate,
  });
}
