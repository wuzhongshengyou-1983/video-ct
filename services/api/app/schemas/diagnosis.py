"""诊断 schemas."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class DiagnosisSubmit(BaseModel):
    video_url: str = Field(..., min_length=4, max_length=1000)
    track: str | None = None
    diagnosis_type: str = "ct_basic"  # ct_basic / ct_full
    title: str | None = None
    description: str | None = None


class DiagnosisOut(BaseModel):
    id: int
    video_url: str
    video_platform: str | None
    status: str
    diagnosis_type: str
    progress_pct: int
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class ReportDimension(BaseModel):
    score: int = Field(..., ge=0, le=100)
    advantages: list[str] = []
    findings: list[str] = []
    suggestions: list[str] = []


class ReportFinding(BaseModel):
    timestamp: str  # "0:07"
    dimension: str
    problem: str
    suggestion: str


class ReportOut(BaseModel):
    id: int
    diagnosis_id: int
    overall_score: int
    grade: str
    dimensions: dict  # {表层观感: ReportDimension, ...}
    findings: list[ReportFinding] = []
    suggestions: list[dict] = []
    benchmark_gap: dict | None = None
    html_path: str | None = None
    pdf_path: str | None = None
    model_used: str | None = None
    user_rating: int | None = None
    consultant_reviewed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ReportFeedback(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = None
