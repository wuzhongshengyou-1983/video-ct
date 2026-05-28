"""账号实体路由 — POST /accounts · GET /accounts/{id}/diagnoses."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.deps import CurrentUser, DbSession
from app.models.account import AccountEntity
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
