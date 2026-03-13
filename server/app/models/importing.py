from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BIGINT_ID, Base, TimestampMixin


class ImportTask(TimestampMixin, Base):
    __tablename__ = "xc_import_task"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    parse_log: Mapped[str | None] = mapped_column(Text)
    ai_log: Mapped[str | None] = mapped_column(Text)
    preview_json: Mapped[dict | None] = mapped_column(JSON)
    operator_id: Mapped[int | None] = mapped_column(BIGINT_ID)
