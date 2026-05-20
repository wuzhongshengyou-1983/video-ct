"""用户路由."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models.user import UserProfile
from app.schemas.user import UserMe, UserProfileIn

router = APIRouter()


@router.put("/me/profile")
async def update_profile(payload: UserProfileIn, db: DbSession, user: CurrentUser):
    if payload.nickname is not None:
        user.nickname = payload.nickname
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url

    res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    prof = res.scalar_one_or_none()
    if not prof:
        prof = UserProfile(user_id=user.id)
        db.add(prof)

    for k in ["track", "platform_main", "follower_count", "bio", "goals"]:
        v = getattr(payload, k, None)
        if v is not None:
            setattr(prof, k, v)

    await db.commit()
    return {"ok": True}
