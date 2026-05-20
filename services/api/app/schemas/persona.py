"""人设 + 商业定位 schemas."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class PersonaScanRequest(BaseModel):
    sample_video_urls: list[str] | None = None  # 用户可选提供视频集
    description: str | None = None  # 用户自述


class PersonaOut(BaseModel):
    id: int
    primary_archetype: str | None
    sub_archetype: str | None
    contrast_point: str | None
    self_tags: dict | None
    audience_tags: dict | None
    scores: dict
    consistency_score: int
    canvas: dict | None
    diagnosis: dict | None
    drift_alert: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PositioningScanRequest(BaseModel):
    description: str | None = None


class PositioningOut(BaseModel):
    id: int
    scores: dict
    monetization_paths: dict
    recommended_archetype: str | None
    recommended_routes: dict | None
    avoid_routes: dict | None
    roadmap_12m: dict | None
    risk_level: int
    canvas_bmc: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
