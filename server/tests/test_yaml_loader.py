from pathlib import Path
import math

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


def test_yaml_tests_have_valid_dim_weights_and_score_rules() -> None:
    store = build_store()
    store.load_all()

    all_tests = store.get_all_tests()
    assert len(all_tests) == 8

    for test_code, test_data in all_tests.items():
        questions = test_data.get("questions", [])
        assert questions, f"{test_code} should contain questions"

        for question in questions:
            question_code = question.get("code") or question.get("seq")
            dim_weights = question.get("dimension_weights")
            if dim_weights is not None:
                assert isinstance(dim_weights, dict), (
                    f"{test_code}:{question_code} dimension_weights must be a mapping"
                )
                for dim_code, raw_weight in dim_weights.items():
                    normalized_dim_code = str(dim_code).strip()
                    assert normalized_dim_code, (
                        f"{test_code}:{question_code} has blank dimension_weights key"
                    )
                    weight = float(raw_weight)
                    assert math.isfinite(weight), (
                        f"{test_code}:{question_code} dimension_weights[{normalized_dim_code}] "
                        "must be finite"
                    )

            for option in question.get("options", []):
                score_rules = option.get("score_rules")
                if score_rules is None:
                    continue

                assert isinstance(score_rules, dict), (
                    f"{test_code}:{question_code}:{option.get('code')} score_rules "
                    "must be a mapping"
                )
                dimension_code = str(score_rules.get("dimension_code", "")).strip()
                assert dimension_code, (
                    f"{test_code}:{question_code}:{option.get('code')} "
                    "score_rules.dimension_code must not be blank"
                )
                score_value = float(score_rules.get("value"))
                assert math.isfinite(score_value), (
                    f"{test_code}:{question_code}:{option.get('code')} "
                    "score_rules.value must be finite"
                )
