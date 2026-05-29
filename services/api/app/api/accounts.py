"""账号实体路由 — POST /accounts · GET /accounts/{id}/diagnoses · GET /accounts/{id}/health."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.exceptions import NotFoundError
from app.deps import CurrentUser, DbSession
from app.models.account import AccountEntity, AccountHealthSnapshot
from app.models.diagnosis import Diagnosis

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    platform: str
    nickname: str | None = None
    platform_account_id: str | None = None
    track: str | None = None
    follower_count: int = 0


class AccountOut(BaseModel):
    id: int
    platform: str
    nickname: str | None
    platform_account_id: str | None
    track: str | None
    follower_count: int
    video_count: int
    is_active: bool

    model_config = {"from_attributes": True}


class DiagnosisBrief(BaseModel):
    id: int
    status: str
    diagnosis_sequence: int | None
    video_url: str
    created_at: str

    model_config = {"from_attributes": True}


# ── 端点 ───────────────────────────────────────────────────────────────────

@router.get("/mine", response_model=list[AccountOut])
async def list_my_accounts(db: DbSession, user: CurrentUser):
    """列出当前用户所有绑定账号."""
    rows = await db.execute(
        select(AccountEntity)
        .where(AccountEntity.user_id == user.id, AccountEntity.is_active == True)
        .order_by(AccountEntity.created_at.desc())
    )
    return [AccountOut.model_validate(a) for a in rows.scalars().all()]


@router.post("", response_model=AccountOut, status_code=201)
async def create_account(payload: AccountCreate, db: DbSession, user: CurrentUser):
    """创建账号实体（绑定当前用户）."""
    account = AccountEntity(
        user_id=user.id,
        platform=payload.platform,
        nickname=payload.nickname,
        platform_account_id=payload.platform_account_id,
        track=payload.track,
        follower_count=payload.follower_count,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return AccountOut.model_validate(account)


@router.get("/{account_id}/diagnoses", response_model=list[DiagnosisBrief])
async def list_account_diagnoses(account_id: int, db: DbSession, user: CurrentUser):
    """返回该账号下当前用户的所有诊断（按时间倒序）."""
    result = await db.execute(
        select(AccountEntity)
        .where(AccountEntity.id == account_id, AccountEntity.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise NotFoundError("账号不存在或无权访问")

    rows = await db.execute(
        select(Diagnosis)
        .where(Diagnosis.account_id == account_id)
        .order_by(Diagnosis.created_at.desc())
    )
    diagnoses = rows.scalars().all()
    return [
        DiagnosisBrief(
            id=d.id,
            status=d.status,
            diagnosis_sequence=d.diagnosis_sequence,
            video_url=d.video_url,
            created_at=d.created_at.isoformat(),
        )
        for d in diagnoses
    ]


@router.get("/{account_id}/health")
async def get_account_health(account_id: int, db: DbSession, user: CurrentUser):
    """账号健康分（Sprint3 数据飞轮）.

    优先返回最新快照；无快照时基于诊断数量派生初始分。
    """
    result = await db.execute(
        select(AccountEntity)
        .where(AccountEntity.id == account_id, AccountEntity.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise NotFoundError("账号不存在或无权访问")

    snap_result = await db.execute(
        select(AccountHealthSnapshot)
        .where(AccountHealthSnapshot.account_entity_id == account_id)
        .order_by(AccountHealthSnapshot.snapshot_date.desc())
        .limit(1)
    )
    snapshot = snap_result.scalar_one_or_none()

    if snapshot:
        return {
            "account_id": account_id,
            "snapshot_date": snapshot.snapshot_date.isoformat(),
            "health_score": snapshot.health_score,
            "dimension_scores": snapshot.dimension_scores,
            "benchmark_percentile": snapshot.benchmark_percentile,
            "trend": snapshot.trend,
            "notes": snapshot.notes,
            "source": "snapshot",
        }

    diag_count = await db.scalar(
        select(func.count(Diagnosis.id)).where(Diagnosis.account_id == account_id)
    ) or 0
    stub_score = min(30.0 + diag_count * 5.0, 60.0)

    return {
        "account_id": account_id,
        "snapshot_date": None,
        "health_score": stub_score,
        "dimension_scores": None,
        "benchmark_percentile": None,
        "trend": "stable",
        "notes": f"基于 {diag_count} 次诊断估算，积累更多数据后自动更新",
        "source": "derived",
    }
