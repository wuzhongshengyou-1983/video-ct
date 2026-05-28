"""视频质量指标（Phase 0 核心·帧级 VMAF/MOS/SEI 数据）."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VideoMetrics(Base):
    """视频帧级质量指标，每条诊断对应一条记录."""
    __tablename__ = "video_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    diagnosis_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("diagnoses.id", ondelete="CASCADE"), unique=True, index=True)

    # 视频基础元数据
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)   # e.g. "1080x1920"
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    bitrate_kbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_mb: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 质量分数（0-100）
    vmaf_score: Mapped[float | None] = mapped_column(Float, nullable=True)      # 视频感知质量
    mos_score: Mapped[float | None] = mapped_column(Float, nullable=True)       # 主观质量评分
    sharpness_score: Mapped[float | None] = mapped_column(Float, nullable=True) # 清晰度
    brightness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    stability_score: Mapped[float | None] = mapped_column(Float, nullable=True) # 防抖

    # 帧级分布（JSON 数组，关键帧采样）
    frame_quality_samples: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sei_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)          # SEI 补充增强信息

    # 平台采集数据
    platform_stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)    # 播放/完播/点赞/评论

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
