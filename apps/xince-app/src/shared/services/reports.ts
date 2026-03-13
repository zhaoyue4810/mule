import type { AppReportDetail, ReportAiStatusPayload } from "@/shared/models/reports";
import { request } from "@/shared/services/http";

export function fetchReportDetail(recordId: number) {
  return request<AppReportDetail>(`/reports/${recordId}`);
}

export function fetchReportAiStatus(recordId: number) {
  return request<ReportAiStatusPayload>(`/reports/${recordId}/ai-status`);
}

export function retryReportAi(recordId: number) {
  return request<ReportAiStatusPayload>("/ai/report/retry", "POST", { record_id: recordId });
}
