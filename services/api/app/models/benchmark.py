"""头部对标库."""
from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Benchmark(Base):
    """头部对标账号库."""
    __tablename__ = "benchmarks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    track: Mapped[str] = mapped_column(String(50), index=True)
    platform: Mapped[str] = mapped_column(String(20))
    account_id: Mapped[str] = mapped_column(String(100))
    nickname: Mapped[str] = mapped_column(String(100))
    follower_count: Mapped[int] = mapped_column(BigInteger, default=0)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    style_archetype: Mapped[str | None] = mapped_column(String(20), nullable=True)
    monetization: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rank_in_track: Mapped[int] = mapped_column(Integer, default=999)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BenchmarkSnapshot(Base):
    """头部数据每日快照."""
    __tablename__ = "benchmark_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    benchmark_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("benchmarks.id", ondelete="CASCADE"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    metrics: Mapped[dict] = mapped_column(JSON)  # 六大指标均值
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
