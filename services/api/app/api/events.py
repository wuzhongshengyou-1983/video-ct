"""行为事件追踪 — POST /api/v1/events/track"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.deps import CurrentUser, DbSession
from app.models.event_log import EventLog

router = APIRouter()


class TrackPayload(BaseModel):
    event_type: str  # report-view / module-dwell / suggestion-copy / suggestion_feedback
    payload: dict[str, Any] | None = None


@router.post("/events/track")
async def track_event(body: TrackPayload, request: Request, db: DbSession, user: CurrentUser):
    """统一行为事件收集，供 v3 数据飞轮使用。"""
    event = EventLog(
        user_id=user.id,
        event_type=body.event_type,
        payload=body.payload,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(event)
    await db.commit()
    return {"ok": True}
