"""商业定位 BPS 档案."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Positioning(Base):
    __tablename__ = "positionings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scores: Mapped[dict] = mapped_column(JSON)  # 6 维评分
    monetization_paths: Mapped[dict] = mapped_column(JSON)  # 6 路径成熟度
    recommended_archetype: Mapped[str | None] = mapped_column(String(30), nullable=True)
    recommended_routes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    avoid_routes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    roadmap_12m: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_level: Mapped[int] = mapped_column(Integer, default=1)
    canvas_bmc: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 商业模式九宫格
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
