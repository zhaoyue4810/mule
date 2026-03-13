from pydantic import BaseModel


class ConfigSummary(BaseModel):
    interaction_type_count: int
    test_count: int
    prompt_group_count: int
    badge_count: int
    soul_fragment_category_count: int
    daily_question_count: int


class InteractionTypeSummary(BaseModel):
    code: str
    title: str
    component: str
    scoring_method: str


class TestSummary(BaseModel):
    test_code: str
    name: str
    category: str
    question_count: int
    dimension_count: int
    source: str


class BootstrapPayload(BaseModel):
    app_name: str
    environment: str
    bootstrap_stage: str
    config_summary: ConfigSummary
    interaction_types: list[InteractionTypeSummary]
    tests: list[TestSummary]
    data_sources: list[str]
    priorities: list[str]
