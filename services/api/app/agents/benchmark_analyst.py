"""对标分析师 Agent · 计算差距 + 异动检测."""
from __future__ import annotations

from app.agents.base import BaseAgent


class BenchmarkAnalystAgent(BaseAgent):
    """对标分析师 · 大部分逻辑是数学，少量 LLM 用于解读."""

    name = "BenchmarkAnalyst"
    role = "行业头部数据分析专家"

    async def run(
        self,
        *,
        user_metrics: dict,  # 用户六大指标
        benchmark_avg: dict,  # 头部均值
        history: list[dict] | None = None,  # 历史差距快照
        tier: str = "free",
    ) -> dict:
        """计算差距 + 趋势 + 异动."""
        gap = {}
        for key in ["曝光率", "点赞率", "评论率", "转发率", "收藏率", "变现率"]:
            user_v = float(user_metrics.get(key, 0))
            bench_v = float(benchmark_avg.get(key, 1))
            if bench_v <= 0:
                gap[key] = 0
            else:
                gap[key] = round((user_v - bench_v) / bench_v * 100, 1)

        # 综合差距百分比（负数=低于头部）
        overall_gap = round(sum(gap.values()) / len(gap), 1)

        # 异动检测（与上月对比）
        alert = None
        if history and len(history) > 0:
            last_overall = history[-1].get("overall_gap", overall_gap)
            delta = overall_gap - last_overall
            if delta < -10:
                alert = {"severity": "warning", "delta": delta, "msg": "整体差距扩大超 10%"}
            elif delta < -5:
                alert = {"severity": "notice", "delta": delta, "msg": "整体差距略有扩大"}

        # 优先级排序
        priorities = sorted(gap.items(), key=lambda x: x[1])[:3]

        return {
            "gap_by_metric": gap,
            "overall_gap_pct": overall_gap,
            "alert": alert,
            "priority_fixes": [{"metric": k, "gap_pct": v} for k, v in priorities],
            "trend": [h.get("overall_gap") for h in (history or [])] + [overall_gap],
        }
