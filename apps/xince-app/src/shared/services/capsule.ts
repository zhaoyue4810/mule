import type { TimeCapsuleCheckPayload, TimeCapsuleItem } from "@/shared/models/capsule";
import { request } from "@/shared/services/http";

export function createTimeCapsule(payload: {
  message: string;
  duration_days: number;
  report_id: number;
}) {
  return request<TimeCapsuleItem>("/capsule/create", "POST", payload);
}

export function fetchTimeCapsules() {
  return request<{ items: TimeCapsuleItem[] }>("/capsule/list");
}

export function revealTimeCapsule(capsuleId: number) {
  return request<{ item: TimeCapsuleItem; revealed: boolean }>(
    `/capsule/${capsuleId}/reveal`,
    "POST",
  );
}

export function checkRevealableCapsules() {
  return request<TimeCapsuleCheckPayload>("/capsule/check");
}
