"""
Phase Gate — 数据量门控系统

各 Phase 功能在数据达标前返回 PHASE_NOT_READY，防止带病上线。

Phase 定义：
  Phase 0 — 代码部署即激活（无门槛）
  Phase 1 — umami_events >= 500（MediaCrawler、账号健康分）
  Phase 2 — suggestion_adoptions >= 10000（Implicit BPR、DuckDB）
  Phase 3 — MAU >= 500 且月收入 >= ¥5000（EconML 因果推断）
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import IntEnum

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class Phase(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3


@dataclass
class PhaseStatus:
    current_phase: Phase
    metrics: dict[str, int | float]
    next_phase: Phase | None
    next_threshold: dict[str, int | float] | None


async def get_current_phase(db: AsyncSession) -> PhaseStatus:
    metrics = await _fetch_metrics(db)

    if metrics["mau"] >= 500 and metrics["monthly_revenue_cny"] >= 5000:
        phase = Phase.THREE
    elif metrics["suggestion_adoptions"] >= 10_000:
        phase = Phase.TWO
    elif metrics["umami_events"] >= 500:
        phase = Phase.ONE
    else:
        phase = Phase.ZERO

    next_phase, next_threshold = _next_phase_info(phase, metrics)
    return PhaseStatus(
        current_phase=phase,
        metrics=metrics,
        next_phase=next_phase,
        next_threshold=next_threshold,
    )


async def require_phase(db: AsyncSession, minimum: Phase) -> bool:
    """
    检查是否达到指定 Phase。

    用法：
        if not await require_phase(db, Phase.ONE):
            raise HTTPException(503, detail="PHASE_NOT_READY")
    """
    status = await get_current_phase(db)
    return status.current_phase >= minimum


async def _fetch_metrics(db: AsyncSession) -> dict[str, int | float]:
    results = await asyncio.gather(
        db.execute(text("SELECT COUNT(*) FROM user_events")),
        db.execute(text("SELECT COUNT(*) FROM suggestion_adoptions")),
        db.execute(
            text("""
                SELECT COUNT(DISTINCT user_id)
                FROM event_logs
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
        ),
        db.execute(
            text("""
                SELECT COALESCE(SUM(paid_cny), 0)
                FROM orders
                WHERE created_at >= date_trunc('month', NOW())
                  AND payment_status = 'paid'
            """)
        ),
    )
    umami_events, adoptions, mau, revenue = [r.scalar() or 0 for r in results]
    return {
        "umami_events": int(umami_events),
        "suggestion_adoptions": int(adoptions),
        "mau": int(mau),
        "monthly_revenue_cny": float(revenue),
    }


def _next_phase_info(
    current: Phase,
    metrics: dict[str, int | float],
) -> tuple[Phase | None, dict[str, int | float] | None]:
    if current == Phase.THREE:
        return None, None
    if current == Phase.TWO:
        return Phase.THREE, {
            "required_mau": 500,
            "required_revenue_cny": 5000,
            "current_mau": metrics["mau"],
            "current_revenue_cny": metrics["monthly_revenue_cny"],
        }
    if current == Phase.ONE:
        return Phase.TWO, {
            "required_suggestion_adoptions": 10_000,
            "current": metrics["suggestion_adoptions"],
        }
    return Phase.ONE, {
        "required_umami_events": 500,
        "current": metrics["umami_events"],
    }
