import type { MemoryGreetingPayload, MemorySuggestPayload } from "@/shared/models/memory";
import { request } from "@/shared/services/http";

export function fetchMemoryGreeting() {
  return request<MemoryGreetingPayload>("/memory/greeting");
}

export function fetchMemorySuggest() {
  return request<MemorySuggestPayload>("/memory/suggest");
}
