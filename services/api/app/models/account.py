"""账号实体 + 健康快照 + 复发问题（v3 Phase 0/1/2 预建）."""
from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AccountEntity(Base):
    """账号实体：跨视频聚合的博主账号（Phase 0）."""
    __tablename__ = "account_entities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    platform: Mapped[str] = mapped_column(String(20))                       # douyin / bilibili / xiaohongshu
    platform_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    track: Mapped[str | None] = mapped_column(String(50), nullable=True)    # 垂类赛道

    follower_count: Mapped[int] = mapped_column(BigInteger, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AccountHealthSnapshot(Base):
    """账号健康分快照（Phase 1 预建）."""
    __tablename__ = "account_health_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_entity_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account_entities.id", ondelete="CASCADE"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)

    health_score: Mapped[float] = mapped_column(Float)                      # 0-100 综合健康分
    dimension_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 各维度分项
    benchmark_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)  # 赛道分位数
    trend: Mapped[str | None] = mapped_column(String(10), nullable=True)    # up / down / stable
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecurringIssue(Base):
    """复发问题检测（Phase 2 预建）."""
    __tablename__ = "recurring_issues"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_entity_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account_entities.id", ondelete="CASCADE"), index=True)

    issue_type: Mapped[str] = mapped_column(String(50), index=True)         # e.g. "low_hook", "no_cta"
    issue_label: Mapped[str] = mapped_column(String(200))
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    diagnosis_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 触发的诊断 ID 列表

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
