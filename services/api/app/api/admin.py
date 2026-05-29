"""管理后台路由."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.core.exceptions import ForbiddenError
from app.deps import CurrentUser, DbSession
from app.models.diagnosis import Diagnosis, Report
from app.models.event_log import EventLog
from app.models.subscription import Order, Subscription
from app.models.user import User

router = APIRouter()


async def require_admin(user: CurrentUser) -> User:
    if user.role not in {"admin", "consultant"}:
        raise ForbiddenError("admin only")
    return user


@router.get("/dashboard")
async def dashboard(db: DbSession, _: User = Depends(require_admin)):
    """CEO 一图看公司."""
    today_start = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
    month_start = today_start.replace(day=1)

    total_users = await db.scalar(select(func.count(User.id))) or 0
    paid_pro = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.tier == "pro", Subscription.status == "active")
    ) or 0
    paid_max = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.tier == "max", Subscription.status == "active")
    ) or 0
    month_revenue = await db.scalar(
        select(func.coalesce(func.sum(Order.paid_cny), 0))
        .where(Order.payment_status == "paid", Order.paid_at >= month_start)
    ) or 0
    today_revenue = await db.scalar(
        select(func.coalesce(func.sum(Order.paid_cny), 0))
        .where(Order.payment_status == "paid", Order.paid_at >= today_start)
    ) or 0
    today_diagnoses = await db.scalar(
        select(func.count(Diagnosis.id)).where(Diagnosis.created_at >= today_start)
    ) or 0
    avg_ai_satisfaction = await db.scalar(
        select(func.coalesce(func.avg(Report.user_rating), 0))
        .where(Report.created_at >= month_start, Report.user_rating.is_not(None))
    ) or 0

    return {
        "total_users": total_users,
        "active_pro": paid_pro,
        "active_max": paid_max,
        "today_revenue_cny": int(today_revenue),
        "month_revenue_cny": int(month_revenue),
        "today_diagnoses": today_diagnoses,
        "avg_ai_satisfaction": round(float(avg_ai_satisfaction), 2),
    }


@router.get("/users")
async def list_users(
    db: DbSession,
    _: User = Depends(require_admin),
    page: int = 1,
    size: int = 20,
    keyword: str | None = None,
):
    q = select(User)
    if keyword:
        q = q.where((User.phone.like(f"%{keyword}%")) | (User.nickname.like(f"%{keyword}%")))
    total = await db.scalar(select(func.count(User.id))) or 0
    res = await db.execute(q.order_by(User.id.desc()).offset((page - 1) * size).limit(size))
    items = res.scalars().all()
    return {
        "items": [
            {
                "id": u.id, "phone": u.phone, "email": u.email,
                "nickname": u.nickname, "role": u.role,
                "is_active": u.is_active, "is_realname": u.is_realname,
                "created_at": u.created_at,
            } for u in items
        ],
        "total": total, "page": page, "size": size,
    }


@router.get("/orders")
async def list_orders(
    db: DbSession,
    _: User = Depends(require_admin),
    page: int = 1, size: int = 20,
):
    total = await db.scalar(select(func.count(Order.id))) or 0
    res = await db.execute(
        select(Order).order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    return {
        "items": [
            {
                "id": o.id, "order_no": o.order_no, "user_id": o.user_id,
                "sku": o.sku, "total_cny": o.total_cny, "paid_cny": o.paid_cny,
                "payment_status": o.payment_status, "paid_at": o.paid_at,
                "referred_by_user_id": o.referred_by_user_id,
                "created_at": o.created_at,
            } for o in res.scalars().all()
        ],
        "total": total, "page": page, "size": size,
    }


@router.get("/stats/events-trend")
async def events_trend(
    db: DbSession,
    _: User = Depends(require_admin),
    days: int = 7,
):
    """event_logs 按日聚合趋势（Sprint3 数据仪表盘）."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(EventLog.created_at).label("day"),
            EventLog.event_type,
            func.count(EventLog.id).label("cnt"),
        )
        .where(EventLog.created_at >= cutoff)
        .group_by(func.date(EventLog.created_at), EventLog.event_type)
        .order_by(func.date(EventLog.created_at))
    )
    rows = result.all()

    day_map: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        day_str = str(row.day)[:10]
        day_map[day_str][row.event_type] += row.cnt

    trend = [
        {"date": day, "total": sum(counts.values()), "by_type": dict(counts)}
        for day, counts in sorted(day_map.items())
    ]

    today = datetime.now(timezone.utc).date().isoformat()
    total_24h = next((item["total"] for item in trend if item["date"] == today), 0)

    return {
        "days": days,
        "trend": trend,
        "phase1_threshold": 1,  # TODO: 内测阶段临时降至 1，正式上线改回 500
        "phase1_met": total_24h >= 1,
    }


@router.get("/diagnoses")
async def list_diagnoses_admin(
    db: DbSession, _: User = Depends(require_admin),
    page: int = 1, size: int = 20,
):
    total = await db.scalar(select(func.count(Diagnosis.id))) or 0
    res = await db.execute(
        select(Diagnosis).order_by(Diagnosis.created_at.desc())
        .offset((page - 1) * size).limit(size)
    )
    return {
        "items": [
            {
                "id": d.id, "user_id": d.user_id, "video_url": d.video_url,
                "status": d.status, "diagnosis_type": d.diagnosis_type,
                "quota_source": d.quota_source, "created_at": d.created_at,
            } for d in res.scalars().all()
        ],
        "total": total, "page": page, "size": size,
    }
