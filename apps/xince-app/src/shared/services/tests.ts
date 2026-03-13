import type {
  PublishedTestDetail,
  PublishedTestQuestionnaire,
  PublishedTestSummary,
  TestSubmitRequest,
  TestSubmitResponse,
} from "@/shared/models/tests";
import { request } from "@/shared/services/http";

export function fetchPublishedTests() {
  return request<PublishedTestSummary[]>("/tests");
}

export function fetchPublishedTestDetail(testCode: string) {
  return request<PublishedTestDetail>(`/tests/${testCode}`);
}

export function fetchPublishedTestQuestionnaire(testCode: string) {
  return request<PublishedTestQuestionnaire>(`/tests/${testCode}/questionnaire`);
}

export function submitTestAnswers(testCode: string, payload: TestSubmitRequest) {
  return request<TestSubmitResponse>(
    `/tests/${testCode}/submit`,
    "POST",
    payload as unknown as Record<string, unknown>,
  );
}
