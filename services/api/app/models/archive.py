"""终身成长档案."""
from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Archive(Base):
    """每个客户一份 · 终身唯一."""
    __tablename__ = "archives"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    archive_no: Mapped[str] = mapped_column(String(40), unique=True)
    track: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_level: Mapped[str] = mapped_column(String(10), default="L1")  # L1-L6
    initial_baseline: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_diagnoses: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ArchiveSnapshot(Base):
    """档案月度快照 · 用于画成长曲线."""
    __tablename__ = "archive_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    archive_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("archives.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    metrics: Mapped[dict] = mapped_column(JSON)  # 六大指标
    benchmark_gap: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 与头部差距 %
    level: Mapped[str] = mapped_column(String(10))
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
