"""顾问助理 Agent · 为 MAX 顾问生成月度/季度简报."""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """你是「顾问助理」，一位专业的短视频运营顾问助手。你的任务是为 MAX 客户的专属顾问准备会议简报。

【输出要求】
- 语言：中文，专业但不冰冷，带有人情味
- brief_title：简洁有力，突出本月/本季核心主题
- key_metrics：从提供的数据中提取关键指标
- gap_progress：与头部差距的变化趋势（收窄/扩大/持平）
- persona_evolution：人设演变概述（稳定/优化/漂移）
- highlights：本月/本季亮点（3-5条，每条 ≤30 字）
- concerns：需关注的风险点（2-4条，每条 ≤30 字）
- recommended_agenda：会议议题建议（3-5个，含时长和备注）
- client_mood_estimate：基于数据趋势推断客户满意度（satisfied/neutral/at_risk）

【注意】
- 不要编造数据，基于提供的实际指标
- 如果某些数据缺失，标注"数据不足"而非猜测
- 语气：专业顾问视角，既要诚实指出问题，也要肯定进步

【输出 JSON Schema】
{
  "brief_title": "...",
  "key_metrics": {"曝光率": ..., "点赞率": ..., "评论率": ..., "转发率": ..., "收藏率": ..., "变现率": ...},
  "gap_progress": {"趋势": "收窄|扩大|持平", "变化说明": "..."},
  "persona_evolution": {"状态": "稳定|优化|漂移", "说明": "..."},
  "highlights": ["亮点1", "亮点2", ...],
  "concerns": ["风险1", "风险2", ...],
  "recommended_agenda": [
    {"topic": "...", "duration_min": 15, "notes": "..."}
  ],
  "client_mood_estimate": "satisfied|neutral|at_risk"
}

严格返回 JSON，不要额外解释。"""


class ConsultantCopilotAgent(BaseAgent):
    """顾问助理 · 为 MAX 顾问准备月度/季度会议简报."""

    name = "ConsultantCopilot"
    role = "短视频运营顾问 AI 助理"

    async def run(
        self,
        *,
        client_id: int,
        meeting_type: str = "monthly",
        user_metrics: dict | None = None,
        gap_history: list[dict] | None = None,
        persona_data: dict | None = None,
        recent_diagnoses: list[dict] | None = None,
        tier: str = "max",
    ) -> dict[str, Any]:
        """生成会议简报.

        参数:
            client_id: 客户 ID
            meeting_type: monthly | quarterly
            user_metrics: 当前用户指标
            gap_history: 历史差距数据（差距追踪）
            persona_data: 人设分析数据
            recent_diagnoses: 最近诊断摘要
            tier: 用户档位
        """
        period_label = "月度" if meeting_type == "monthly" else "季度"

        # 构建结构化输入
        user_msg_parts = [
            f"请为 {period_label} 顾问会议准备简报：",
            "",
            f"客户 ID：{client_id}",
            f"会议类型：{period_label}",
            "",
            "【当前指标】",
            f"{user_metrics or '数据不足'}",
            "",
            "【与头部差距变化趋势】",
            f"{gap_history or '数据不足'}",
            "",
            "【人设演变数据】",
            f"{persona_data or '数据不足'}",
            "",
            "【最近诊断摘要】",
            f"{recent_diagnoses or '暂无诊断记录'}",
        ]
        user_msg = "\n".join(str(p) for p in user_msg_parts)

        data, meta = await self._llm_json(
            system=SYSTEM_PROMPT,
            user=user_msg,
            tier=tier,
            temperature=0.3,
        )

        # 校验 + 兜底
        data = self._validate_and_fill(data, meeting_type)
        data["_meta"] = meta
        return data

    @staticmethod
    def _validate_and_fill(data: dict, meeting_type: str) -> dict:
        """校验输出 schema 并兜底."""
        data.setdefault("brief_title", f"{'月度' if meeting_type == 'monthly' else '季度'}运营简报")
        data.setdefault("key_metrics", {})
        data.setdefault("gap_progress", {"趋势": "持平", "变化说明": "数据不足"})
        data.setdefault("persona_evolution", {"状态": "稳定", "说明": "数据不足"})
        data.setdefault("highlights", [])
        data.setdefault("concerns", [])
        data.setdefault("recommended_agenda", [
            {"topic": "本期数据回顾", "duration_min": 10, "notes": "过一遍关键指标"},
            {"topic": "差距分析", "duration_min": 10, "notes": "对标头部差距变化"},
            {"topic": "下期优化方向", "duration_min": 15, "notes": "制定行动计划"},
        ])

        # 校验 client_mood_estimate
        valid_moods = {"satisfied", "neutral", "at_risk"}
        if data.get("client_mood_estimate") not in valid_moods:
            data["client_mood_estimate"] = "neutral"

        # 校验 agenda
        for item in data.get("recommended_agenda", []):
            item.setdefault("duration_min", 10)
            item.setdefault("notes", "")

        return data
