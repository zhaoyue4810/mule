from __future__ import annotations

from pydantic import BaseModel, Field


class AdminYamlFileStatus(BaseModel):
    file_name: str
    status: str
    item_count: int = 0
    updated_at: str | None = None


class AdminYamlStatusResponse(BaseModel):
    files: list[AdminYamlFileStatus]
    summary: dict[str, int]
    badge_definitions: dict[str, dict] = Field(default_factory=dict)


class AdminBadgeDefinitionItem(BaseModel):
    badge_key: str
    name: str
    emoji: str
    type: str
    unlock_rule: dict
    yaml_source: str | None = None
