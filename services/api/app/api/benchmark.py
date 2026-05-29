"""头部对标路由."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.agents.benchmark_analyst import BenchmarkAnalystAgent
from app.deps import CurrentUser, DbSession
from app.models.benchmark import Benchmark
from app.services.llm_router import llm_router
from app.services.viral_dna_service import analyze_viral_dna
from loguru import logger

router = APIRouter()


@router.get("/tracks")
async def list_tracks(db: DbSession):
    """所有可对标的细分赛道."""
    res = await db.execute(select(Benchmark.track).distinct())
    return [{"track": t[0]} for t in res.all()]


@router.get("/top10/{track}")
async def top10(track: str, db: DbSession):
    """某赛道头部 10 名."""
    res = await db.execute(
        select(Benchmark).where(Benchmark.track == track, Benchmark.is_active.is_(True))
        .order_by(Benchmark.rank_in_track).limit(10)
    )
    items = res.scalars().all()
    return [
        {
            "rank": b.rank_in_track,
            "account_id": b.account_id,
            "nickname": b.nickname,
            "platform": b.platform,
            "follower_count": b.follower_count,
            "avatar_url": b.avatar_url,
            "bio": b.bio,
            "style_archetype": b.style_archetype,
            "monetization": b.monetization,
        }
        for b in items
    ]


@router.post("/gap")
async def compute_gap(
    track: str,
    user_metrics: dict,
    db: DbSession,
    user: CurrentUser,
):
    """计算用户六大指标与赛道头部均值的差距."""
    # 简化版头部均值（生产从 benchmark_snapshots 算）
    benchmark_avg = {
        "曝光率": 8.0, "点赞率": 5.5, "评论率": 1.2,
        "转发率": 0.8, "收藏率": 2.3, "变现率": 3.0,
    }
    agent = BenchmarkAnalystAgent()
    result = await agent.run(
        user_metrics=user_metrics, benchmark_avg=benchmark_avg,
        history=[], tier="free",
    )
    return result


@router.post("/viral-dna")
async def get_viral_dna(
    db: DbSession,
    user: CurrentUser,
    diagnosis_id: int | None = None,
    track: str | None = None,
):
    """分析赛道头部竞品的爆火 DNA.

    track 可选：优先从 diagnosis_id 对应的 video_meta 中自动推导，缺省用 '通用'。
    """
    from app.models.diagnosis import Diagnosis as DiagnosisModel

    if track is None:
        if diagnosis_id:
            res = await db.execute(
                select(DiagnosisModel).where(
                    DiagnosisModel.id == diagnosis_id, DiagnosisModel.user_id == user.id
                )
            )
            diag = res.scalar_one_or_none()
            track = (diag.video_meta or {}).get("track") or "通用" if diag else "通用"
        else:
            track = "通用"

    # 从 benchmark 表取该赛道 rank=1 的竞品
    res = await db.execute(
        select(Benchmark)
        .where(Benchmark.track == track, Benchmark.is_active.is_(True))
        .order_by(Benchmark.rank_in_track)
        .limit(1)
    )
    top = res.scalar_one_or_none()

    if top is None:
        # 赛道暂无数据，用赛道名称作为占位昵称
        competitor_nickname = f"{track}头部账号"
        bio_summary = None
    else:
        competitor_nickname = top.nickname
        bio_summary = top.bio

    follower_count = top.follower_count if top is not None else 0

    result = await analyze_viral_dna(
        competitor_nickname=competitor_nickname,
        track=track,
        competitor_follower_count=follower_count,
        diagnosis_summary=bio_summary,
    )
    return result.to_dict()


class RemixRequest(BaseModel):
    track: str
    viral_dna: dict


@router.post("/remix")
async def generate_remix(
    body: RemixRequest,
    db: DbSession,
    user: CurrentUser,
):
    """基于爆火 DNA 生成二创剧本."""
    track = body.track
    viral_dna = body.viral_dna
    competitor_nickname = viral_dna.get("competitor_nickname", f"{track}头部账号")
    # 提取 top_factors 摘要供 LLM 参考
    top_factors_text = ""
    if isinstance(viral_dna.get("top_factors"), list):
        top_factors_text = "\n".join(
            f"- {f.get('name', '')}: {f.get('evidence', '')}"
            for f in viral_dna["top_factors"][:3]
        )

    prompt = f"""你是一名短视频内容策划，擅长基于竞品爆款的底层逻辑生成二创剧本。

【赛道】{track}
【参考竞品】{competitor_nickname}
【爆火 DNA 核心因子】
{top_factors_text or "（暂无）"}

请生成一套完整的二创剧本，分为 5-7 个 segment，每个 segment 包含：
- stage：阶段名称（如"钩子"/"展开"/"转折"/"高潮"/"CTA"）
- duration：时长（如"0-3s"）
- function：该段的功能定位（如"制造悬念"/"建立信任"/"触发情绪"，15 字以内）
- script：台词/旁白建议（50 字以内）
- shot：镜头/画面建议（30 字以内）
- why：为什么这样设计（参考竞品哪个爆点，20 字以内）

只返回纯 JSON，格式：
{{"segments": [
  {{"stage": "钩子", "duration": "0-3s", "function": "制造悬念", "script": "...", "shot": "...", "why": "..."}}
]}}"""

    messages = [
        {
            "role": "system",
            "content": "你是一名短视频内容策划专家。请只输出纯 JSON，不加任何 markdown 格式。",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        resp = await llm_router.chat(
            messages=messages,
            tier="free",
            task="chat",
            response_format="json_object",
            temperature=0.5,
            max_tokens=2048,
        )
        data = resp.as_json()
        segments = data.get("segments", [])
        if not isinstance(segments, list) or not segments:
            raise ValueError("segments 解析为空")
    except Exception as exc:
        logger.warning(f"[Remix] LLM 调用失败，返回空剧本: {exc}")
        segments = [
            {
                "stage": "钩子",
                "duration": "0-3s",
                "function": "（暂无）",
                "script": "（剧本生成暂时不可用，请稍后重试）",
                "shot": "（暂无建议）",
                "why": "服务降级",
            }
        ]

    return {"segments": segments}


@router.get("/topics/{track}")
async def get_trending_topics(track: str, user: CurrentUser):
    """获取赛道热门选题（LLM 生成，TikHub 搜索端点待后续接入）."""
    prompt = f"""你是一名短视频选题策划，熟悉各赛道的爆款规律。

请为「{track}」赛道生成 5 个当前最具爆款潜力的选题，每个选题包含：
- title：选题标题（20 字以内，有吸引力）
- hotness：热度指数 0-100（基于当前平台趋势估算）
- why_hot：为什么这个选题容易爆（30 字以内）
- how_to：如何做这个选题（30 字以内，给创作者的建议）
- risk：潜在风险或注意事项（20 字以内）

只返回纯 JSON，格式：
{{"topics": [
  {{"title": "...", "hotness": 88, "why_hot": "...", "how_to": "...", "risk": "..."}}
]}}"""

    messages = [
        {
            "role": "system",
            "content": "你是一名短视频选题策划专家。请只输出纯 JSON，不加任何 markdown 格式。",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        resp = await llm_router.chat(
            messages=messages,
            tier="free",
            task="chat",
            response_format="json_object",
            temperature=0.6,
            max_tokens=1024,
        )
        data = resp.as_json()
        topics = data.get("topics", [])
        if not isinstance(topics, list) or not topics:
            raise ValueError("topics 解析为空")
    except Exception as exc:
        logger.warning(f"[Topics] LLM 调用失败，返回默认选题: {exc}")
        topics = [
            {
                "title": f"{track}热门选题（暂时不可用）",
                "hotness": 0,
                "why_hot": "服务降级，请稍后重试",
                "how_to": "暂无建议",
                "risk": "暂无",
            }
        ]

    return {"track": track, "topics": topics[:5]}
