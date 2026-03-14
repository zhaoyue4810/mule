"""SQLAlchemy model registry."""


def import_all_models() -> None:
    from app.models import ai  # noqa: F401
    from app.models import badge  # noqa: F401
    from app.models import calendar  # noqa: F401
    from app.models import importing  # noqa: F401
    from app.models import match  # noqa: F401
    from app.models import record  # noqa: F401
    from app.models import report  # noqa: F401
    from app.models import soul  # noqa: F401
    from app.models import test  # noqa: F401
    from app.models import user  # noqa: F401
