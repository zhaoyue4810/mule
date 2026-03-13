from fastapi import APIRouter

from app.core.config import get_settings
from app.core.yaml_loader import yaml_config
from app.schemas.bootstrap import (
    BootstrapPayload,
    ConfigSummary,
    InteractionTypeSummary,
    TestSummary,
)

router = APIRouter(tags=["bootstrap"])


@router.get("/bootstrap", response_model=BootstrapPayload)
def get_bootstrap() -> BootstrapPayload:
    settings = get_settings()
    summary = yaml_config.summary()

    interaction_types = [
        InteractionTypeSummary(
            code=code,
            title=item.get("title", code),
            component=item.get("component", ""),
            scoring_method=item.get("scoring_method", "unknown"),
        )
        for code, item in yaml_config.get_interaction_types().items()
    ]

    tests = [
        TestSummary(
            test_code=item["test_code"],
            name=item["name"],
            category=item["category"],
            question_count=len(item.get("questions", [])),
            dimension_count=len(item.get("dimensions", [])),
            source=item.get("source", "yaml"),
        )
        for item in yaml_config.get_all_tests().values()
    ]

    return BootstrapPayload(
        app_name=settings.app_name,
        environment=settings.app_env,
        bootstrap_stage="phase_2_content_runtime",
        config_summary=ConfigSummary(**summary),
        interaction_types=interaction_types,
        tests=tests,
        data_sources=[
            "xince-technical-design-final_121644ff.md",
            "xince-design-doc.docx",
            "index.html",
        ],
        priorities=[
            "Expose published test list/detail APIs for the user app.",
            "Initialize the uni-app user application shell.",
            "Build the answer container and question rendering protocol.",
        ],
    )


@router.get("/config/interaction-types", response_model=list[InteractionTypeSummary])
def get_interaction_types() -> list[InteractionTypeSummary]:
    return [
        InteractionTypeSummary(
            code=code,
            title=item.get("title", code),
            component=item.get("component", ""),
            scoring_method=item.get("scoring_method", "unknown"),
        )
        for code, item in yaml_config.get_interaction_types().items()
    ]


@router.get("/config/tests", response_model=list[TestSummary])
def get_tests() -> list[TestSummary]:
    return [
        TestSummary(
            test_code=item["test_code"],
            name=item["name"],
            category=item["category"],
            question_count=len(item.get("questions", [])),
            dimension_count=len(item.get("dimensions", [])),
            source=item.get("source", "yaml"),
        )
        for item in yaml_config.get_all_tests().values()
    ]
