"""人设 IPP 档案."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Persona(Base):
    """每次 IPP 扫描产出一条 · 形成历史快照."""
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    primary_archetype: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sub_archetype: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contrast_point: Mapped[str | None] = mapped_column(String(200), nullable=True)
    self_tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    audience_tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scores: Mapped[dict] = mapped_column(JSON)  # 6 维评分
    consistency_score: Mapped[int] = mapped_column(Integer)
    canvas: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 人设画布 9 模块
    diagnosis: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 病灶 + 建议
    drift_alert: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
