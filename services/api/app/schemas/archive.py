"""成长档案 schemas."""
from __future__ import annotations

from datetime import datetime, date
from pydantic import BaseModel


class ArchiveOut(BaseModel):
    id: int
    archive_no: str
    track: str | None
    current_level: str  # L1-L6
    initial_baseline: dict | None
    total_diagnoses: int
    created_at: datetime

    class Config:
        from_attributes = True


class ArchiveSnapshotOut(BaseModel):
    snapshot_date: date
    metrics: dict
    benchmark_gap: dict | None
    level: str
    overall_score: int | None
    notes: str | None

    class Config:
        from_attributes = True


class GrowthCurveOut(BaseModel):
    metrics: dict  # 六大指标历史曲线
    benchmark_gap_curve: list[dict]
    level_history: list[dict]
    diagnoses_count: int
    days_active: int
