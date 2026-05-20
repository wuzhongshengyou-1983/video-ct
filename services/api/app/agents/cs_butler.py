"""客户成功管家 Agent · 生命周期事件 → 运营动作推荐."""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent

# 生命周期事件 → 推荐动作映射（无需 LLM 的规则层）
LIFECYCLE_RULES: dict[str, dict[str, Any]] = {
    "registered": {
        "recommended_action": "send_push",
        "priority": "P1",
        "channel": "wechat_push",
        "urgency": "today",
        "reason": "新用户注册后 24h 内激活率最高，发送欢迎消息 + 引导首次诊断",
    },
    "first_scan": {
        "recommended_action": "send_push",
        "priority": "P1",
        "channel": "wechat_push",
        "urgency": "now",
        "reason": "首次诊断完成后立即推送结果解读引导，提升付费转化窗口",
    },
    "first_paid": {
        "recommended_action": "consultant_call",
        "priority": "P0",
        "channel": "consultant_wechat",
        "urgency": "today",
        "reason": "首付客户是高价值信号，顾问 24h 内触达可大幅提升留存率",
    },
    "renewal_due": {
        "recommended_action": "coupon_offer",
        "priority": "P0",
        "channel": "wechat_push",
        "urgency": "this_week",
        "reason": "续费到期前 7 天，优惠券+顾问跟进组合策略效果最佳",
    },
    "churn_risk": {
        "recommended_action": "consultant_call",
        "priority": "P0",
        "channel": "consultant_wechat",
        "urgency": "now",
        "reason": "流失风险信号需立即人工干预，顾问电话/企微沟通挽留",
    },
    "upgrade_ready": {
        "recommended_action": "send_push",
        "priority": "P1",
        "channel": "wechat_push",
        "urgency": "this_week",
        "reason": "用量已达免费/PRO上限，推送升级引导 + 限时优惠",
    },
    "engagement_drop": {
        "recommended_action": "send_push",
        "priority": "P1",
        "channel": "wechat_push",
        "urgency": "this_week",
        "reason": "用户活跃度下降，推送新功能或案例内容重新激活",
    },
    "negative_feedback": {
        "recommended_action": "consultant_call",
        "priority": "P0",
        "channel": "consultant_wechat",
        "urgency": "now",
        "reason": "负面反馈需立即人工跟进，了解问题并给出解决方案",
    },
    "milestone_reached": {
        "recommended_action": "send_push",
        "priority": "P2",
        "channel": "wechat_push",
        "urgency": "this_week",
        "reason": "里程碑达成（如第10次诊断），发送祝贺+社交分享激励",
    },
    "inactive_30d": {
        "recommended_action": "send_push",
        "priority": "P1",
        "channel": "sms",
        "urgency": "this_week",
        "reason": "30天未活跃，多通道触达（推送+SMS），提供回归奖励",
    },
}

SYSTEM_PROMPT = """你是「客户成功管家」，短视频 SaaS 平台的客户运营专家。

你的任务是基于给定的生命周期事件和客户上下文，生成一条可用于推送/企微/短信的文案模板。

【文案要求】
- 长度：≤100 字（短信 ≤70 字）
- 语气：温暖、专业、不推销感过重
- 包含可行动作引导（如"去看看"、"点击查看"）
- 适当个性化（提到客户所在赛道或昵称）
- 不要包含任何敏感承诺（"必涨粉"等）

【输出格式】
{"message_template": "文案内容"}

严格返回 JSON。不要额外解释。"""


class CSButlerAgent(BaseAgent):
    """客户成功管家 · 根据生命周期事件推荐运营动作 + 生成消息模板."""

    name = "CSButler"
    role = "短视频 SaaS 客户成功运营管家"

    async def run(
        self,
        *,
        client_id: int,
        lifecycle_event: str,
        client_context: dict | None = None,
        tier: str = "free",
    ) -> dict[str, Any]:
        """推荐运营动作 + 生成消息模板.

        参数:
            client_id: 客户 ID
            lifecycle_event: 生命周期事件类型
            client_context: 客户上下文（昵称/赛道/最近动态等）
            tier: 用户档位
        """
        ctx = client_context or {}

        # 1. 规则层：确定推荐动作
        rule = LIFECYCLE_RULES.get(lifecycle_event)
        if rule is None:
            rule = {
                "recommended_action": "no_action",
                "priority": "P2",
                "channel": "wechat_push",
                "urgency": "this_week",
                "reason": f"未识别的事件类型 '{lifecycle_event}'，建议人工判断",
            }

        # 2. LLM 层：生成消息模板
        user_msg = f"""请为以下客户生成消息推送文案：

【客户信息】
- 昵称：{ctx.get('nickname', '用户')}
- 赛道：{ctx.get('track', '通用')}
- 生命周期事件：{lifecycle_event}
- 推荐动作：{rule['recommended_action']}
- 触达通道：{rule['channel']}
- 紧急度：{rule['urgency']}
- 理由：{rule['reason']}

请生成适合{rule['channel']}通道的文案模板。"""

        try:
            data, meta = await self._llm_json(
                system=SYSTEM_PROMPT,
                user=user_msg,
                tier=tier,
                temperature=0.5,
            )
            message_template = data.get("message_template", "")
        except Exception:
            # LLM 失败时用规则兜底模板
            message_template = self._fallback_template(
                lifecycle_event, rule, ctx
            )

        return {
            "recommended_action": rule["recommended_action"],
            "priority": rule["priority"],
            "message_template": message_template,
            "channel": rule["channel"],
            "urgency": rule["urgency"],
            "reason": rule["reason"],
        }

    @staticmethod
    def _fallback_template(
        event: str, rule: dict, ctx: dict
    ) -> str:
        """LLM 不可用时的兜底消息模板."""
        nickname = ctx.get("nickname", "用户")
        templates: dict[str, str] = {
            "registered": f"Hi {nickname}，欢迎加入视频CT！点击开始你的首个免费诊断，看看你的账号在哪个段位 →",
            "first_scan": f"{nickname}，你的首份CT诊断报告已生成！点击查看详细病灶分析和修复建议 →",
            "first_paid": f"{nickname}，恭喜升级PRO！你的专属顾问将在24小时内联系你，请留意企微消息。",
            "renewal_due": f"{nickname}，你的PRO会员即将到期，续费享专属优惠券已到账，点击查看 →",
            "churn_risk": f"{nickname}，我们注意到你最近使用不多，有什么我们可以帮你的吗？专属顾问随时待命。",
            "upgrade_ready": f"{nickname}，你的免费诊断次数已用完。升级PRO解锁无限诊断+专属顾问 →",
            "engagement_drop": f"{nickname}，好久不见！我们上线了新功能，来看看有哪些新玩法 →",
            "negative_feedback": f"{nickname}，感谢你的反馈！专属顾问会尽快联系你了解详情并解决。",
            "milestone_reached": f"恭喜{nickname}！你已完成第10次诊断，分享你的成长轨迹给朋友吧 →",
            "inactive_30d": f"{nickname}，你的账号已30天未活跃，回归即享专属福利，点击查看 →",
        }
        return templates.get(event, f"Hi {nickname}，{rule['reason']}")
