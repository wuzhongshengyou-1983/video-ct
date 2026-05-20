"""商业定位 BPS 路由."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.agents.biz_strategist import BizStrategistAgent
from app.deps import CurrentUser, DbSession
from app.models.positioning import Positioning
from app.models.user import UserProfile
from app.schemas.persona import PositioningOut, PositioningScanRequest
from app.services.subscription_service import get_user_tier

router = APIRouter()


@router.post("/scan", response_model=PositioningOut)
async def scan(payload: PositioningScanRequest, db: DbSession, user: CurrentUser):
    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    prof = prof_res.scalar_one_or_none()
    tier = await get_user_tier(db, user.id)

    agent = BizStrategistAgent()
    result = await agent.run(
        track=prof.track if prof and prof.track else "通用",
        follower_count=prof.follower_count if prof else 0,
        current_monetization=prof.monetization_paths if prof else "",
        goals=(prof.goals if prof else "") or (payload.description or ""),
        tier=tier,
    )
    bps = Positioning(
        user_id=user.id,
        scores=result["scores"],
        monetization_paths=result["monetization_paths"],
        recommended_archetype=result.get("recommended_archetype"),
        recommended_routes=result.get("recommended_routes"),
        avoid_routes=result.get("avoid_routes"),
        roadmap_12m=result.get("roadmap_12m"),
        risk_level=result.get("risk_level", 2),
        canvas_bmc=result.get("canvas_bmc"),
    )
    db.add(bps)
    await db.commit()
    await db.refresh(bps)
    return PositioningOut.model_validate(bps)


@router.get("/me", response_model=PositioningOut | None)
async def my_positioning(db: DbSession, user: CurrentUser):
    res = await db.execute(
        select(Positioning).where(Positioning.user_id == user.id)
        .order_by(Positioning.created_at.desc()).limit(1)
    )
    p = res.scalar_one_or_none()
    return PositioningOut.model_validate(p) if p else None
