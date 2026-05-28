"""v3 Phase 0 — 新增 5 张表 + diagnoses 表 2 列

Revision ID: 001
Revises: None
Create Date: 2026-05-28

新增：
- account_entities       — 账号实体（跨视频聚合）
- video_metrics          — 视频帧级质量指标
- benchmark_daily_stats  — 头部账号日度快照
- account_health_snapshots — 账号健康分快照（Phase 1 预建）
- recurring_issues       — 复发问题检测（Phase 2 预建）

ALTER diagnoses:
- ADD COLUMN account_id BIGINT NULL
- ADD COLUMN diagnosis_sequence INT NULL DEFAULT 0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. account_entities ────────────────────────────────────────────────
    op.create_table(
        "account_entities",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("platform_account_id", sa.String(100), nullable=True),
        sa.Column("nickname", sa.String(100), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("track", sa.String(50), nullable=True),
        sa.Column("follower_count", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("video_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("meta", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_account_entities_user_id", "account_entities", ["user_id"])

    # ── 2. video_metrics ───────────────────────────────────────────────────
    op.create_table(
        "video_metrics",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("diagnosis_id", sa.BigInteger, sa.ForeignKey("diagnoses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("duration_sec", sa.Float, nullable=True),
        sa.Column("resolution", sa.String(20), nullable=True),
        sa.Column("fps", sa.Float, nullable=True),
        sa.Column("bitrate_kbps", sa.Integer, nullable=True),
        sa.Column("file_size_mb", sa.Float, nullable=True),
        sa.Column("vmaf_score", sa.Float, nullable=True),
        sa.Column("mos_score", sa.Float, nullable=True),
        sa.Column("sharpness_score", sa.Float, nullable=True),
        sa.Column("brightness_score", sa.Float, nullable=True),
        sa.Column("stability_score", sa.Float, nullable=True),
        sa.Column("frame_quality_samples", sa.JSON, nullable=True),
        sa.Column("sei_data", sa.JSON, nullable=True),
        sa.Column("platform_stats", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_video_metrics_diagnosis_id", "video_metrics", ["diagnosis_id"], unique=True)

    # ── 3. benchmark_daily_stats ───────────────────────────────────────────
    op.create_table(
        "benchmark_daily_stats",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("benchmark_id", sa.BigInteger, sa.ForeignKey("benchmarks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stat_date", sa.Date, nullable=False),
        sa.Column("follower_count", sa.BigInteger, nullable=True),
        sa.Column("new_followers", sa.Integer, nullable=True),
        sa.Column("video_count", sa.Integer, nullable=True),
        sa.Column("avg_play_count", sa.BigInteger, nullable=True),
        sa.Column("avg_like_count", sa.BigInteger, nullable=True),
        sa.Column("avg_comment_count", sa.Integer, nullable=True),
        sa.Column("avg_share_count", sa.Integer, nullable=True),
        sa.Column("avg_completion_rate", sa.Float, nullable=True),
        sa.Column("top_video_url", sa.String(500), nullable=True),
        sa.Column("raw", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_benchmark_daily_stats_benchmark_id", "benchmark_daily_stats", ["benchmark_id"])
    op.create_index("ix_benchmark_daily_stats_stat_date", "benchmark_daily_stats", ["stat_date"])

    # ── 4. account_health_snapshots ────────────────────────────────────────
    op.create_table(
        "account_health_snapshots",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("account_entity_id", sa.BigInteger, sa.ForeignKey("account_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("health_score", sa.Float, nullable=False),
        sa.Column("dimension_scores", sa.JSON, nullable=True),
        sa.Column("benchmark_percentile", sa.Float, nullable=True),
        sa.Column("trend", sa.String(10), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_account_health_snapshots_account_entity_id", "account_health_snapshots", ["account_entity_id"])
    op.create_index("ix_account_health_snapshots_snapshot_date", "account_health_snapshots", ["snapshot_date"])

    # ── 5. recurring_issues ────────────────────────────────────────────────
    op.create_table(
        "recurring_issues",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("account_entity_id", sa.BigInteger, sa.ForeignKey("account_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_type", sa.String(50), nullable=False),
        sa.Column("issue_label", sa.String(200), nullable=False),
        sa.Column("occurrence_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("diagnosis_ids", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recurring_issues_account_entity_id", "recurring_issues", ["account_entity_id"])
    op.create_index("ix_recurring_issues_issue_type", "recurring_issues", ["issue_type"])

    # ── 6. ALTER diagnoses — 2 新列 ────────────────────────────────────────
    op.add_column("diagnoses", sa.Column("account_id", sa.BigInteger, sa.ForeignKey("account_entities.id", ondelete="SET NULL"), nullable=True))
    op.add_column("diagnoses", sa.Column("diagnosis_sequence", sa.Integer, nullable=True, server_default="0"))
    op.create_index("ix_diagnoses_account_id", "diagnoses", ["account_id"])


def downgrade() -> None:
    op.drop_index("ix_diagnoses_account_id", "diagnoses")
    op.drop_column("diagnoses", "diagnosis_sequence")
    op.drop_column("diagnoses", "account_id")

    op.drop_index("ix_recurring_issues_issue_type", "recurring_issues")
    op.drop_index("ix_recurring_issues_account_entity_id", "recurring_issues")
    op.drop_table("recurring_issues")

    op.drop_index("ix_account_health_snapshots_snapshot_date", "account_health_snapshots")
    op.drop_index("ix_account_health_snapshots_account_entity_id", "account_health_snapshots")
    op.drop_table("account_health_snapshots")

    op.drop_index("ix_benchmark_daily_stats_stat_date", "benchmark_daily_stats")
    op.drop_index("ix_benchmark_daily_stats_benchmark_id", "benchmark_daily_stats")
    op.drop_table("benchmark_daily_stats")

    op.drop_index("ix_video_metrics_diagnosis_id", "video_metrics")
    op.drop_table("video_metrics")

    op.drop_index("ix_account_entities_user_id", "account_entities")
    op.drop_table("account_entities")
