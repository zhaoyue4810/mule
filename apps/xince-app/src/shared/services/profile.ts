import type {
  AppProfileOverview,
  ProfileReportHistoryItem,
} from "@/shared/models/profile";
import { request } from "@/shared/services/http";

export function fetchMyProfileOverview() {
  return request<AppProfileOverview>("/profile/me/overview");
}

export function fetchMyProfileReports() {
  return request<ProfileReportHistoryItem[]>("/profile/me/reports");
}

export function fetchProfileOverview(userId: number) {
  return request<AppProfileOverview>(`/profile/${userId}/overview`);
}

export function fetchProfileReports(userId: number) {
  return request<ProfileReportHistoryItem[]>(`/profile/${userId}/reports`);
}
