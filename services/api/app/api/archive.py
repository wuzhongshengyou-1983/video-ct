"""成长档案路由."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.deps import CurrentUser, DbSession
from app.models.archive import Archive, ArchiveSnapshot
from app.schemas.archive import ArchiveOut, ArchiveSnapshotOut, GrowthCurveOut

router = APIRouter()


@router.get("/me", response_model=ArchiveOut | None)
async def my_archive(db: DbSession, user: CurrentUser):
    res = await db.execute(select(Archive).where(Archive.user_id == user.id))
    archive = res.scalar_one_or_none()
    return ArchiveOut.model_validate(archive) if archive else None


@router.get("/me/curve", response_model=GrowthCurveOut)
async def growth_curve(db: DbSession, user: CurrentUser):
    res = await db.execute(
        select(ArchiveSnapshot).where(ArchiveSnapshot.user_id == user.id)
        .order_by(ArchiveSnapshot.snapshot_date)
    )
    snaps = res.scalars().all()

    metrics_curve = {k: [] for k in ["曝光率", "点赞率", "评论率", "转发率", "收藏率", "变现率"]}
    gap_curve = []
    level_history = []
    for s in snaps:
        for k in metrics_curve:
            metrics_curve[k].append({"date": s.snapshot_date.isoformat(), "value": s.metrics.get(k, 0)})
        gap_curve.append({
            "date": s.snapshot_date.isoformat(),
            "gap_pct": (s.benchmark_gap or {}).get("overall_gap_pct", 0),
        })
        level_history.append({"date": s.snapshot_date.isoformat(), "level": s.level})

    from app.models.diagnosis import Diagnosis
    from sqlalchemy import func
    diag_count = await db.scalar(
        select(func.count(Diagnosis.id)).where(Diagnosis.user_id == user.id)
    ) or 0
    days_active = len({s.snapshot_date for s in snaps})

    return GrowthCurveOut(
        metrics=metrics_curve,
        benchmark_gap_curve=gap_curve,
        level_history=level_history,
        diagnoses_count=diag_count,
        days_active=days_active,
    )
