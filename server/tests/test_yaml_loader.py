from pathlib import Path

from app.core.yaml_loader import YamlConfigStore


def build_store() -> YamlConfigStore:
    config_dir = Path(__file__).resolve().parents[1] / "app" / "config"
    return YamlConfigStore(config_dir)


def test_yaml_loader_loads_core_config() -> None:
    store = build_store()
    store.load_all()

    summary = store.summary()

    assert summary["interaction_type_count"] == 15
    assert summary["test_count"] == 8
    assert summary["prompt_group_count"] == 3
    assert summary["badge_count"] >= 3
    assert summary["daily_question_count"] >= 3


def test_yaml_loader_micro_feedback() -> None:
    store = build_store()
    store.load_all()

    message = store.get_micro_feedback("swipe", "right")
    assert isinstance(message, str)
    assert message
