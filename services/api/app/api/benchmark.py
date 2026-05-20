"""头部对标路由."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.agents.benchmark_analyst import BenchmarkAnalystAgent
from app.deps import CurrentUser, DbSession
from app.models.benchmark import Benchmark

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
