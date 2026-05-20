"""管理后台路由."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.core.exceptions import ForbiddenError
from app.deps import CurrentUser, DbSession
from app.models.diagnosis import Diagnosis, Report
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
