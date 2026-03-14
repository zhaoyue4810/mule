import type { PublishedTestSummary } from "@/shared/models/tests";

export interface MemoryGreetingPayload {
  greeting: string;
  mood: string;
  know_level: number;
  test_count: number;
  behavior_tags: string[];
}

export interface MemorySuggestPayload {
  title: string;
  reason: string;
  items: PublishedTestSummary[];
}
