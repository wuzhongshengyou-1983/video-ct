"""AI 直接调用路由（如生成钩子/标题/封面）."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.agents.content_maker import ContentMakerAgent
from app.deps import CurrentUser, DbSession
from app.models.persona import Persona
from app.models.user import UserProfile
from app.services.subscription_service import get_user_tier

router = APIRouter()


class GenerateRequest(BaseModel):
    topic: str
    track: str | None = None


@router.post("/content/generate")
async def gen_content(payload: GenerateRequest, db: DbSession, user: CurrentUser):
    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    prof = prof_res.scalar_one_or_none()
    persona_res = await db.execute(
        select(Persona).where(Persona.user_id == user.id)
        .order_by(Persona.created_at.desc()).limit(1)
    )
    persona = persona_res.scalar_one_or_none()
    tier = await get_user_tier(db, user.id)

    agent = ContentMakerAgent()
    result = await agent.run(
        topic=payload.topic,
        track=payload.track or (prof.track if prof else "通用"),
        persona_archetype=persona.primary_archetype if persona else None,
        tier=tier,
    )
    return result


@router.get("/agents")
async def list_agents():
    """所有可用 Agent 元数据."""
    return {
        "agents": [
            {"name": "CTRadiologist", "role": "6 维 CT 诊断官", "tier_min": "free"},
            {"name": "BenchmarkAnalyst", "role": "头部对标分析师", "tier_min": "free"},
            {"name": "PersonaScout", "role": "人设 IPP 观察员", "tier_min": "free"},
            {"name": "BizStrategist", "role": "商业定位策略师", "tier_min": "pro"},
            {"name": "ContentMaker", "role": "内容生成手", "tier_min": "free"},
            {"name": "DataSentinel", "role": "数据预警员", "tier_min": "max"},
            {"name": "ConsultantCopilot", "role": "顾问助理", "tier_min": "internal"},
            {"name": "CustomerSuccessButler", "role": "客户成功管家", "tier_min": "internal"},
        ]
    }
