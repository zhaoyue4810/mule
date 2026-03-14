from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.app_content import PublishedTestSummary


class MemoryGreetingPayload(BaseModel):
    greeting: str
    mood: str
    know_level: int
    test_count: int
    behavior_tags: list[str] = Field(default_factory=list)


class MemorySuggestPayload(BaseModel):
    title: str
    reason: str
    items: list[PublishedTestSummary] = Field(default_factory=list)
