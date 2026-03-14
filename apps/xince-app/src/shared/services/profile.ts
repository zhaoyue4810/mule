import type {
  AppProfileOverview,
  DailyQuestionStatePayload,
  OnboardingProfilePayload,
  ProfileSettingsPayload,
  ProfileReportHistoryItem,
} from "@/shared/models/profile";
import { request } from "@/shared/services/http";

export interface UpdateOnboardingProfileRequest {
  nickname: string;
  avatar_value: string;
  bio: string;
  gender: number;
  birth_year?: number | null;
  birth_month?: number | null;
}

export function fetchMyProfileOverview() {
  return request<AppProfileOverview>("/profile/me/overview");
}

export function fetchMyProfileSettings() {
  return request<ProfileSettingsPayload>("/profile/me/settings");
}

export function updateMyProfileSettings(payload: ProfileSettingsPayload) {
  return request<ProfileSettingsPayload>("/profile/me/settings", "PUT", {
    ...payload,
  });
}

export function fetchMyOnboardingProfile() {
  return request<OnboardingProfilePayload>("/profile/me/onboarding");
}

export function updateMyOnboardingProfile(payload: UpdateOnboardingProfileRequest) {
  return request<OnboardingProfilePayload>("/profile/me/onboarding", "PUT", {
    ...payload,
  });
}

export function fetchMyProfileReports() {
  return request<ProfileReportHistoryItem[]>("/profile/me/reports");
}

export function fetchMyDailyQuestion() {
  return request<DailyQuestionStatePayload>("/profile/me/daily-question");
}

export function submitMyDailyQuestion(
  questionId: number,
  answerIndex: number,
  answerDate?: string,
) {
  return request<DailyQuestionStatePayload>(
    "/profile/me/daily-question",
    "POST",
    {
      question_id: questionId,
      answer_index: answerIndex,
      answer_date: answerDate,
    },
  );
}

export function fetchProfileOverview(userId: number) {
  return request<AppProfileOverview>(`/profile/${userId}/overview`);
}

export function fetchProfileReports(userId: number) {
  return request<ProfileReportHistoryItem[]>(`/profile/${userId}/reports`);
}
