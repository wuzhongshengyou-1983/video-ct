"""人设 IPP 路由."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.agents.persona_scout import PersonaScoutAgent
from app.deps import CurrentUser, DbSession
from app.models.persona import Persona
from app.models.user import UserProfile
from app.schemas.persona import PersonaOut, PersonaScanRequest
from app.services.subscription_service import get_user_tier

router = APIRouter()


@router.post("/scan", response_model=PersonaOut)
async def scan(payload: PersonaScanRequest, db: DbSession, user: CurrentUser):
    # 用户 profile
    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    prof = prof_res.scalar_one_or_none()
    tier = await get_user_tier(db, user.id)

    agent = PersonaScoutAgent()
    result = await agent.run(
        videos_summary=" ; ".join(payload.sample_video_urls or []),
        comments_summary="",
        user_description=payload.description or (prof.bio if prof else ""),
        track=prof.track if prof and prof.track else "通用",
        tier=tier,
    )
    persona = Persona(
        user_id=user.id,
        primary_archetype=result.get("primary_archetype"),
        sub_archetype=result.get("sub_archetype"),
        contrast_point=result.get("contrast_point"),
        self_tags=result.get("self_tags"),
        audience_tags=result.get("audience_tags"),
        scores=result["scores"],
        consistency_score=result["consistency_score"],
        canvas=result.get("canvas"),
        diagnosis=result.get("diagnosis"),
        drift_alert=result.get("drift_alert", False),
    )
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return PersonaOut.model_validate(persona)


@router.get("/me", response_model=PersonaOut | None)
async def my_persona(db: DbSession, user: CurrentUser):
    res = await db.execute(
        select(Persona).where(Persona.user_id == user.id)
        .order_by(Persona.created_at.desc()).limit(1)
    )
    p = res.scalar_one_or_none()
    return PersonaOut.model_validate(p) if p else None


@router.get("/archetypes")
async def list_archetypes():
    return {
        "气场型": ["行业权威", "反差大佬", "凶猛敢说"],
        "干货型": ["教学派", "拆解派", "资源派"],
        "共情型": ["闺蜜型", "治愈系", "共同体"],
        "趣味型": ["段子手", "鬼马少年", "反差萌"],
    }
