from __future__ import annotations

from pydantic import BaseModel, Field


class PersonaCardDimensionItem(BaseModel):
    dim_code: str
    label: str
    score: float


class PersonaCardWeather(BaseModel):
    emoji: str
    title: str
    description: str


class PersonaCardPayload(BaseModel):
    user_id: int
    nickname: str
    avatar_value: str
    persona_title: str
    soul_signature: str
    keywords: list[str] = Field(default_factory=list)
    dimensions: list[PersonaCardDimensionItem] = Field(default_factory=list)
    weather: PersonaCardWeather
