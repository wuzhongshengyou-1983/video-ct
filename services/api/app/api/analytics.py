"""埋点事件接收端点.

POST /api/v1/analytics/events — 接收批量埋点事件，写入 event_logs 表。
不做实时处理，只存储。
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.deps import DbSession, CurrentUserOptional

router = APIRouter()


class TrackEventItem(BaseModel):
    event: str = Field(..., description="事件名，如 page_view:home")
    properties: dict | None = Field(None, description="事件属性")
    user_id: int | None = Field(None, description="用户 ID")
    timestamp: int = Field(..., description="事件时间戳 (ms)")


class TrackEventsRequest(BaseModel):
    events: list[TrackEventItem] = Field(..., min_length=1, max_length=100, description="批量事件列表")


@router.post("/analytics/events", status_code=204)
async def receive_events(
    body: TrackEventsRequest,
    db: DbSession,
    request: Request,
    _current_user: CurrentUserOptional = None,
):
    """接收批量埋点事件。

    不做实时处理，直接写入 event_logs 表。
    前端可匿名发送（未登录时 user_id 为 null）。
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")[:500]

    insert_sql = text("""
        INSERT INTO event_logs (user_id, event_type, payload, ip, user_agent)
        VALUES (:user_id, :event_type, :payload, :ip, :user_agent)
    """)

    for item in body.events:
        params = {
            "user_id": item.user_id,
            "event_type": item.event,
            "payload": json.dumps(item.properties) if item.properties else None,
            "ip": client_ip,
            "user_agent": user_agent,
        }
        await db.execute(insert_sql, params)

    await db.commit()
