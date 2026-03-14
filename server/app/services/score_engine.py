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
    def normalize_numeric_answer(
        interaction_type: str,
        numeric_value: float,
        config: dict | None,
    ) -> float:
        if interaction_type == "swipe":
            return 1.0 if numeric_value >= 1 else 0.0

        if interaction_type in {"slider", "star", "hotcold", "pressure", "colorpick"}:
            config = config or {}
            min_value = float(config.get("min", 0 if interaction_type == "pressure" else 1))
            max_value = float(
                config.get(
                    "max",
                    config.get(
                        (
                            "max_duration"
                            if interaction_type == "pressure"
                            else "max_hue"
                            if interaction_type == "colorpick"
                            else "max_stars"
                        ),
                        (
                            3000
                            if interaction_type == "pressure"
                            else 360
                            if interaction_type == "colorpick"
                            else 5
                        ),
                    ),
                )
            )
            if max_value <= min_value:
                return numeric_value
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
            config = config or {}
            min_value = float(config.get("min", 1))
            max_value = float(config.get("max", 5))
            if numeric_value < min_value or numeric_value > max_value:
                raise ValueError(
                    f"Question type {interaction_type} requires value between {min_value} and {max_value}"
                )
            if interaction_type == "hotcold" and not float(numeric_value).is_integer():
                raise ValueError("Question type hotcold requires integer steps")

        if interaction_type == "star":
            config = config or {}
            min_value = float(config.get("min", 1))
            max_value = float(config.get("max_stars", 5))
            if numeric_value < min_value or numeric_value > max_value:
                raise ValueError(
                    f"Question type star requires value between {min_value} and {max_value}"
                )
            if not float(numeric_value).is_integer():
                raise ValueError("Question type star requires integer steps")

        if interaction_type == "pressure":
            config = config or {}
            min_value = float(config.get("min", 0))
            max_value = float(config.get("max_duration", 3000))
            if numeric_value < min_value or numeric_value > max_value:
                raise ValueError(
                    f"Question type pressure requires value between {min_value} and {max_value}"
                )
            if not float(numeric_value).is_integer():
                raise ValueError("Question type pressure requires integer milliseconds")

        if interaction_type == "colorpick":
            config = config or {}
            min_value = float(config.get("min_hue", 0))
            max_value = float(config.get("max_hue", 360))
            if numeric_value < min_value or numeric_value > max_value:
                raise ValueError(
                    f"Question type colorpick requires value between {min_value} and {max_value}"
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
