"""事件日志（审计 + 行为埋点合一）."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventLog(Base):
    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)  # diagnosis.submitted 等
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
