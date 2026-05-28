"""诊断任务 + 报告."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Diagnosis(Base):
    """诊断任务（每次提交一条视频 = 一个诊断）."""
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    video_url: Mapped[str] = mapped_column(String(1000))
    video_platform: Mapped[str | None] = mapped_column(String(20), nullable=True)
    video_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 标题、时长、封面、播放数等
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued / processing / done / failed
    diagnosis_type: Mapped[str] = mapped_column(String(20), default="ct_basic")  # ct_basic / ct_full / persona / positioning
    quota_source: Mapped[str] = mapped_column(String(20), default="free")  # free / single / pro / max
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # v3 Phase 0 — 账号关联
    account_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("account_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    diagnosis_sequence: Mapped[int] = mapped_column(Integer, nullable=True, default=0)  # 同账号第几次诊断


class Report(Base):
    """诊断报告（一次 diagnosis 对应一份 report）."""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    diagnosis_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("diagnoses.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    overall_score: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(10))  # L1-L6
    dimensions: Mapped[dict] = mapped_column(JSON)  # 6 维评分
    findings: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 病灶定位（含时间戳）
    suggestions: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 修复建议清单
    benchmark_gap: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 与对标差距
    html_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    user_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    user_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultant_reviewed: Mapped[bool] = mapped_column(default=False)
    consultant_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
