"""诊断 + 报告路由."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.database import SessionLocal
from app.deps import CurrentUser, DbSession
from app.models.diagnosis import Diagnosis, Report
from app.schemas.diagnosis import (
    DiagnosisOut, DiagnosisSubmit, ReportFeedback, ReportOut
)
from app.services import diagnosis_service

router = APIRouter()


async def _bg_run(diag_id: int):
    """后台跑诊断（生产环境用 Celery）."""
    async with SessionLocal() as session:
        try:
            await diagnosis_service.run_full_pipeline(session, diag_id)
        except Exception:
            pass  # 已在 service 内 log + 标 failed


@router.post("/submit", response_model=DiagnosisOut)
async def submit(payload: DiagnosisSubmit, bg: BackgroundTasks, db: DbSession, user: CurrentUser):
    diag = await diagnosis_service.create_diagnosis(
        db, user=user, video_url=payload.video_url,
        track=payload.track, diagnosis_type=payload.diagnosis_type,
    )
    await db.commit()
    await db.refresh(diag)
    # 后台跑
    bg.add_task(_bg_run, diag.id)
    return DiagnosisOut.model_validate(diag)


@router.get("/{diagnosis_id}", response_model=DiagnosisOut)
async def get_diagnosis(diagnosis_id: int, db: DbSession, user: CurrentUser):
    res = await db.execute(
        select(Diagnosis).where(Diagnosis.id == diagnosis_id, Diagnosis.user_id == user.id)
    )
    diag = res.scalar_one_or_none()
    if not diag:
        raise NotFoundError("diagnosis")
    return DiagnosisOut.model_validate(diag)


@router.get("/", response_model=list[DiagnosisOut])
async def list_diagnoses(db: DbSession, user: CurrentUser, limit: int = 20):
    res = await db.execute(
        select(Diagnosis).where(Diagnosis.user_id == user.id)
        .order_by(Diagnosis.created_at.desc()).limit(limit)
    )
    return [DiagnosisOut.model_validate(d) for d in res.scalars().all()]


@router.get("/{diagnosis_id}/report", response_model=ReportOut)
async def get_report(diagnosis_id: int, db: DbSession, user: CurrentUser):
    res = await db.execute(
        select(Report).where(Report.diagnosis_id == diagnosis_id, Report.user_id == user.id)
    )
    report = res.scalar_one_or_none()
    if not report:
        raise NotFoundError("report")
    return ReportOut.model_validate(report)


@router.post("/{diagnosis_id}/report/feedback")
async def submit_feedback(
    diagnosis_id: int, payload: ReportFeedback, db: DbSession, user: CurrentUser
):
    res = await db.execute(
        select(Report).where(Report.diagnosis_id == diagnosis_id, Report.user_id == user.id)
    )
    report = res.scalar_one_or_none()
    if not report:
        raise NotFoundError("report")
    report.user_rating = payload.rating
    report.user_feedback = payload.feedback
    await db.commit()
    return {"ok": True}


@router.post("/{diagnosis_id}/resubmit", response_model=DiagnosisOut)
async def resubmit(diagnosis_id: int, bg: BackgroundTasks, db: DbSession, user: CurrentUser):
    """复诊：基于已有诊断重新提交同一视频，自动追踪改善对比。"""
    res = await db.execute(
        select(Diagnosis).where(Diagnosis.id == diagnosis_id, Diagnosis.user_id == user.id)
    )
    original = res.scalar_one_or_none()
    if not original:
        raise NotFoundError("diagnosis")

    meta = dict(original.video_meta or {})
    meta["parent_diagnosis_id"] = diagnosis_id

    new_diag = await diagnosis_service.create_diagnosis(
        db,
        user=user,
        video_url=original.video_url,
        track=original.video_meta.get("track") if original.video_meta else None,
        diagnosis_type=original.diagnosis_type,
    )
    new_diag.video_meta = meta
    await db.commit()
    await db.refresh(new_diag)
    bg.add_task(_bg_run, new_diag.id)
    return DiagnosisOut.model_validate(new_diag)
