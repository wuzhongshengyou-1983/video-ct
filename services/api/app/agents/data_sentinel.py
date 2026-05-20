"""数据预警员 Agent · 异动检测 + 分级告警 · 数学为主，LLM 解读为辅."""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent

# 异动阈值配置
THRESHOLDS: dict[str, dict[str, float]] = {
    "曝光率": {"notice": 10, "warning": 20, "critical": 35},
    "点赞率": {"notice": 10, "warning": 20, "critical": 35},
    "评论率": {"notice": 15, "warning": 30, "critical": 50},
    "转发率": {"notice": 15, "warning": 30, "critical": 50},
    "收藏率": {"notice": 10, "warning": 20, "critical": 35},
    "变现率": {"notice": 10, "warning": 25, "critical": 40},
    "粉丝增长率": {"notice": 10, "warning": 20, "critical": 35},
    "完播率": {"notice": 10, "warning": 20, "critical": 35},
}

SEVERITY_ORDER = {"critical": 0, "warning": 1, "notice": 2}


def _classify_delta(metric: str, delta_pct: float) -> str | None:
    """根据指标 + 变化百分比判定严重级别."""
    thresholds = THRESHOLDS.get(metric, {"notice": 10, "warning": 20, "critical": 35})
    abs_delta = abs(delta_pct)
    if abs_delta >= thresholds["critical"]:
        return "critical"
    if abs_delta >= thresholds["warning"]:
        return "warning"
    if abs_delta >= thresholds["notice"]:
        return "notice"
    return None


def _overall_status(alerts: list[dict]) -> str:
    """从告警列表推断整体状态."""
    if not alerts:
        return "green"
    severities = {a["severity"] for a in alerts}
    if "critical" in severities:
        return "red"
    if "warning" in severities:
        return "orange"
    if "notice" in severities:
        return "yellow"
    return "green"


SUGGESTED_ACTIONS: dict[str, dict[str, str]] = {
    "曝光率": {
        "critical": "立即检查封面/标题/开头3秒，对比同赛道爆款，A/B测试新封面",
        "warning": "关注曝光趋势，准备备选封面方案，检查发布时间段",
        "notice": "持续观察曝光变化，微调标题关键词",
    },
    "点赞率": {
        "critical": "诊断内容质量：观点是否有争议性？情绪共鸣是否到位？参考CT诊断病灶修复",
        "warning": "分析点赞率下滑的视频内容特征，调整选题方向",
        "notice": "保持内容品质，关注互动引导话术",
    },
    "评论率": {
        "critical": "在视频结尾增加开放式提问，设计争议性观点引发讨论",
        "warning": "检查评论区运营：是否及时回复？是否有引导话术？",
        "notice": "增加评论区互动，置顶引导性评论",
    },
    "转发率": {
        "critical": "提升内容实用价值或情感共鸣，检查是否有转发诱因（干货/情感/争议）",
        "warning": "在视频中加入转发引导文案，优化分享卡片",
        "notice": "关注转发数据，识别高转发内容特征",
    },
    "收藏率": {
        "critical": "增强内容的工具属性：清单/步骤/模板类内容收藏率更高",
        "warning": "优化内容的可复用性，增加「收藏备用」类引导",
        "notice": "在内容中加入可收藏的实用信息点",
    },
    "变现率": {
        "critical": "变现链路检查：商品页是否加载正常？转化路径有无断点？",
        "warning": "优化商品展示时机和话术，A/B测试不同变现引导方式",
        "notice": "持续优化变现漏斗，关注转化率波动",
    },
    "粉丝增长率": {
        "critical": "人设是否出现漂移？检查最近内容方向与账号定位一致性",
        "warning": "分析粉丝净增趋势，关注取关原因",
        "notice": "保持发稿频率和质量稳定",
    },
    "完播率": {
        "critical": "开头3秒钩子力度不足，中间节奏拖沓，检查视频时长是否过长",
        "warning": "优化前5秒内容，检查BGM和节奏是否匹配",
        "notice": "监控完播率变化，微调节奏和时长",
    },
}

SYSTEM_PROMPT = """你是「数据预警员」，短视频运营数据异动检测专家。

你的任务是：基于已计算出的告警列表和指标数据，生成一段业务可读的总结摘要。

【要求】
- 用中文，≤150 字
- 突出最严重的告警（如有）
- 如果整体状态 green，给出肯定性评价
- 不提具体数值，用趋势性语言（"明显下滑"、"略有波动"、"持续向好"）

【输出格式】
{"summary": "一段总结"}
严格返回 JSON，不要额外解释。"""


class DataSentinelAgent(BaseAgent):
    """数据预警员 · 接收用户指标数据，检测异动并生成分级告警."""

    name = "DataSentinel"
    role = "短视频数据异动检测与预警专家"

    async def run(
        self,
        *,
        user_metrics: dict[str, float],
        baseline: dict[str, float] | None = None,
        thresholds_override: dict[str, dict[str, float]] | None = None,
        tier: str = "free",
    ) -> dict[str, Any]:
        """执行数据异动检测.

        参数:
            user_metrics: 当前指标数据 {"曝光率": 12.3, "点赞率": 4.5, ...}
            baseline: 基线数据（环比/同比），默认使用 user_metrics 自身（无基线时跳过）
            thresholds_override: 可选的自定义阈值
            tier: 用户档位
        """
        thresholds = thresholds_override or THRESHOLDS
        ref = baseline or {}

        # 1. 计算每个指标的 delta 并生成告警
        alerts: list[dict] = []
        for metric, current_val in user_metrics.items():
            base_val = ref.get(metric)
            if base_val is None or base_val == 0:
                continue
            delta_pct = round((current_val - base_val) / base_val * 100, 1)
            severity = _classify_delta(metric, delta_pct)
            if severity is None:
                continue
            direction = "上升" if delta_pct > 0 else "下降"
            actions = SUGGESTED_ACTIONS.get(metric, {})
            suggested_action = actions.get(
                severity,
                f"关注{metric}{direction}趋势，建议人工复核",
            )
            alerts.append({
                "severity": severity,
                "metric": metric,
                "delta_pct": delta_pct,
                "message": f"{metric}{direction}{abs(delta_pct):.1f}%（基线 {base_val} → 当前 {current_val}）",
                "suggested_action": suggested_action,
            })

        # 按严重程度排序
        alerts.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 99))

        overall = _overall_status(alerts)

        # 2. 用 LLM 生成总结摘要
        summary = ""
        if alerts:
            alert_summary_text = "\n".join(
                f"- [{a['severity']}] {a['message']}" for a in alerts[:6]
            )
            user_msg = f"""请为以下告警生成总结（≤150 字）：

整体状态：{overall}
告警列表：
{alert_summary_text}

当前指标：{user_metrics}
基线指标：{ref or '无基线数据'}
"""
            try:
                data, meta = await self._llm_json(
                    system=SYSTEM_PROMPT,
                    user=user_msg,
                    tier=tier,
                    temperature=0.3,
                )
                summary = data.get("summary", "")
            except Exception:
                # LLM 失败时生成数学兜底摘要
                summary = self._fallback_summary(overall, alerts)
        else:
            summary = "所有指标运行平稳，未检测到明显异动，数据表现良好。"

        return {
            "alerts": alerts,
            "overall_status": overall,
            "summary": summary,
        }

    @staticmethod
    def _fallback_summary(overall: str, alerts: list[dict]) -> str:
        """LLM 不可用时，用规则生成兜底摘要."""
        status_map = {
            "red": "数据出现重大异动，多项关键指标严重偏离基线，需立即排查。",
            "orange": "部分指标出现较大波动，建议关注并准备应对方案。",
            "yellow": "个别指标略有波动，整体可控，建议持续观察。",
            "green": "所有指标运行平稳，整体数据表现良好。",
        }
        base = status_map.get(overall, "数据正常。")
        if alerts:
            top = alerts[0]
            base += f" 最需关注：{top['metric']}（{top['severity']}级别）。"
        return base
