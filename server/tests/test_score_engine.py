from app.services.score_engine import ScoreEngine


def test_colorpick_accepts_numeric_answer_shape() -> None:
    ScoreEngine.validate_answer_shape(
        "colorpick",
        option_code=None,
        numeric_value=180,
        ordered_option_codes=None,
        point=None,
    )


def test_rank_requires_ordered_option_codes_only() -> None:
    try:
        ScoreEngine.validate_answer_shape(
            "rank",
            option_code="a",
            numeric_value=None,
            ordered_option_codes=["a", "b"],
            point=None,
        )
    except ValueError as exc:
        assert "only accepts ordered_option_codes" in str(exc)
    else:
        raise AssertionError("Expected rank answer validation to fail")


def test_plot2d_requires_both_coordinates() -> None:
    try:
        ScoreEngine.validate_point({"x": 0.3})
    except ValueError as exc:
        assert "requires both x and y" in str(exc)
    else:
        raise AssertionError("Expected plot2d point validation to fail")


def test_plot2d_rejects_non_finite_coordinates() -> None:
    try:
        ScoreEngine.validate_point({"x": float("nan"), "y": 0.4})
    except ValueError as exc:
        assert "point.x must be a finite number" in str(exc)
    else:
        raise AssertionError("Expected non-finite plot2d point validation to fail")


def test_colorpick_rejects_invalid_step() -> None:
    try:
        ScoreEngine.validate_numeric_range(
            "colorpick",
            numeric_value=17,
            config={"min_hue": 0, "max_hue": 360, "step": 15},
        )
    except ValueError as exc:
        assert "requires step 15.0" in str(exc)
    else:
        raise AssertionError("Expected colorpick step validation to fail")


def test_numeric_normalization_uses_configured_colorpick_bounds() -> None:
    normalized = ScoreEngine.normalize_numeric_answer(
        "colorpick",
        numeric_value=180,
        config={"min_hue": 0, "max_hue": 360},
    )

    assert normalized == 0.5
