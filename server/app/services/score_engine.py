from __future__ import annotations

import math


class ScoreEngine:
    NUMERIC_INTERACTION_TYPES = {
        "swipe",
        "slider",
        "star",
        "hotcold",
        "pressure",
        "colorpick",
    }

    @staticmethod
    def _ensure_finite_number(field_name: str, value: float) -> None:
        if not math.isfinite(value):
            raise ValueError(f"{field_name} must be a finite number")

    @staticmethod
    def _validate_step(field_name: str, value: float, min_value: float, step: float) -> None:
        if step <= 0:
            return
        quotient = (value - min_value) / step
        if not math.isclose(quotient, round(quotient), rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(f"{field_name} requires step {step}")

    @classmethod
    def _resolve_numeric_constraints(
        cls,
        interaction_type: str,
        config: dict | None,
    ) -> tuple[float, float, float]:
        config = config or {}

        if interaction_type in {"slider", "hotcold"}:
            min_value = float(config.get("min", 1))
            max_value = float(config.get("max", 5))
            step = float(config.get("step", 1))
        elif interaction_type == "star":
            min_value = float(config.get("min", 1))
            max_value = float(config.get("max_stars", 5))
            step = float(config.get("step", 1))
        elif interaction_type == "pressure":
            min_value = float(config.get("min", 0))
            max_value = float(config.get("max_duration", 3000))
            step = float(config.get("step", 1))
        elif interaction_type == "colorpick":
            min_value = float(config.get("min_hue", 0))
            max_value = float(config.get("max_hue", 360))
            step = float(config.get("step", 1))
        else:
            raise ValueError(f"Unsupported numeric interaction type: {interaction_type}")

        cls._ensure_finite_number(f"{interaction_type}.min", min_value)
        cls._ensure_finite_number(f"{interaction_type}.max", max_value)
        cls._ensure_finite_number(f"{interaction_type}.step", step)

        if max_value <= min_value:
            raise ValueError(
                f"Question type {interaction_type} has invalid numeric config: max must be greater than min"
            )
        if step <= 0:
            raise ValueError(
                f"Question type {interaction_type} has invalid numeric config: step must be greater than 0"
            )

        return min_value, max_value, step

    @staticmethod
    def normalize_numeric_answer(
        interaction_type: str,
        numeric_value: float,
        config: dict | None,
    ) -> float:
        if interaction_type == "swipe":
            return 1.0 if numeric_value >= 1 else 0.0

        if interaction_type in {"slider", "star", "hotcold", "pressure", "colorpick"}:
            min_value, max_value, _ = ScoreEngine._resolve_numeric_constraints(
                interaction_type,
                config,
            )
            return (numeric_value - min_value) / (max_value - min_value)

        return numeric_value

    @classmethod
    def expects_numeric_answer(cls, interaction_type: str) -> bool:
        return interaction_type in cls.NUMERIC_INTERACTION_TYPES

    @classmethod
    def validate_answer_shape(
        cls,
        interaction_type: str,
        option_code: str | None,
        numeric_value: float | None,
        ordered_option_codes: list[str] | None,
        point: dict[str, float] | None,
    ) -> None:
        expects_numeric = cls.expects_numeric_answer(interaction_type)
        if expects_numeric:
            if numeric_value is None:
                raise ValueError(
                    f"Question type {interaction_type} requires numeric_value"
                )
            if (
                option_code is not None
                or ordered_option_codes is not None
                or point is not None
            ):
                raise ValueError(
                    f"Question type {interaction_type} only accepts numeric_value"
                )
            return

        if interaction_type == "rank":
            if not ordered_option_codes:
                raise ValueError("Question type rank requires ordered_option_codes")
            if option_code is not None or numeric_value is not None or point is not None:
                raise ValueError("Question type rank only accepts ordered_option_codes")
            return

        if interaction_type == "plot2d":
            if point is None:
                raise ValueError("Question type plot2d requires point")
            if (
                option_code is not None
                or numeric_value is not None
                or ordered_option_codes is not None
            ):
                raise ValueError("Question type plot2d only accepts point")
            return

        if not option_code:
            raise ValueError(
                f"Question type {interaction_type} requires option_code"
            )
        if numeric_value is not None or ordered_option_codes is not None or point is not None:
            raise ValueError(
                f"Question type {interaction_type} only accepts option_code"
            )

    @classmethod
    def validate_numeric_range(
        cls,
        interaction_type: str,
        numeric_value: float,
        config: dict | None,
    ) -> None:
        cls._ensure_finite_number("numeric_value", numeric_value)

        if interaction_type == "swipe" and numeric_value not in {0, 1}:
            raise ValueError("Question type swipe only accepts 0 or 1")

        if interaction_type in {"slider", "hotcold"}:
            min_value, max_value, step = cls._resolve_numeric_constraints(
                interaction_type,
                config,
            )
            if numeric_value < min_value or numeric_value > max_value:
                raise ValueError(
                    f"Question type {interaction_type} requires value between {min_value} and {max_value}"
                )
            cls._validate_step(
                f"Question type {interaction_type}",
                numeric_value,
                min_value,
                step,
            )

        if interaction_type == "star":
            min_value, max_value, step = cls._resolve_numeric_constraints(
                interaction_type,
                config,
            )
            if numeric_value < min_value or numeric_value > max_value:
                raise ValueError(
                    f"Question type star requires value between {min_value} and {max_value}"
                )
            cls._validate_step("Question type star", numeric_value, min_value, step)

        if interaction_type == "pressure":
            min_value, max_value, step = cls._resolve_numeric_constraints(
                interaction_type,
                config,
            )
            if numeric_value < min_value or numeric_value > max_value:
                raise ValueError(
                    f"Question type pressure requires value between {min_value} and {max_value}"
                )
            cls._validate_step(
                "Question type pressure",
                numeric_value,
                min_value,
                step,
            )

        if interaction_type == "colorpick":
            min_value, max_value, step = cls._resolve_numeric_constraints(
                interaction_type,
                config,
            )
            if numeric_value < min_value or numeric_value > max_value:
                raise ValueError(
                    f"Question type colorpick requires value between {min_value} and {max_value}"
                )
            cls._validate_step(
                "Question type colorpick",
                numeric_value,
                min_value,
                step,
            )

    @staticmethod
    def normalize_rank_position(index: int, total: int) -> float:
        if total <= 1:
            return 1.0
        return 1.0 - index / (total - 1)

    @staticmethod
    def validate_point(point: dict[str, float]) -> None:
        x = point.get("x")
        y = point.get("y")
        if x is None or y is None:
            raise ValueError("Question type plot2d requires both x and y")
        ScoreEngine._ensure_finite_number("point.x", float(x))
        ScoreEngine._ensure_finite_number("point.y", float(y))
        if x < 0 or x > 1 or y < 0 or y > 1:
            raise ValueError("Question type plot2d requires x and y between 0 and 1")
