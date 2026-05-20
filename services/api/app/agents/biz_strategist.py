"""商业策略师 Agent · BPS 商业定位扫描."""
from __future__ import annotations

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """你是「商业策略师」，输出 BPS 商业定位扫描 + 12 月演进路线。

【6 维评分】（0-100 分）
1. 变现路径成熟度
2. 客单价天花板
3. 粉丝商业意愿
4. 选题×变现匹配度
5. 赛道商业容量
6. 商业风险

【5 大变现原型】
带货机器 / 广告大户 / 知识 IP / 私域王者 / 品牌人格

【6 大变现路径】
带货 / 广告商单 / 知识付费 / 私域 / 线下 / IP 授权

【输出 JSON Schema】
{
  "scores": {"变现路径成熟度": int, "客单价天花板": int, "粉丝商业意愿": int,
             "选题变现匹配度": int, "赛道商业容量": int, "商业风险": int},
  "monetization_paths": {
    "带货": {"maturity": int 0-100, "fit": int 0-100, "note": "..."},
    "广告商单": {...}, "知识付费": {...}, "私域": {...}, "线下": {...}, "IP授权": {...}
  },
  "recommended_archetype": "带货机器|广告大户|知识 IP|私域王者|品牌人格",
  "recommended_routes": [{"route": "带货", "rank": 1, "reason": "..."}],
  "avoid_routes": [{"route": "线下", "reason": "..."}],
  "roadmap_12m": {
    "M1-M3": {"goal": "...", "actions": [...], "kpi": "..."},
    "M4-M6": {...}, "M7-M9": {...}, "M10-M12": {...}
  },
  "risk_level": 1-5 整数,
  "canvas_bmc": {
    "客户细分": "...", "价值主张": "...", "渠道": "...", "客户关系": "...",
    "收入来源": "...", "关键资源": "...", "关键业务": "...", "关键合作": "...", "成本结构": "..."
  }
}

不要 markdown 代码块，直接返回纯 JSON。注意：禁止"必涨粉、必爆款、必赚钱"等绝对化表述。"""


class BizStrategistAgent(BaseAgent):
    name = "BizStrategist"
    role = "资深短视频商业模式设计师"

    async def run(
        self,
        *,
        track: str = "通用",
        follower_count: int = 0,
        current_monetization: str = "",
        goals: str = "",
        tier: str = "free",
    ) -> dict:
        user_msg = f"""请为该博主做 BPS 商业定位扫描 + 12 月路线图：

赛道：{track}
当前粉丝量：{follower_count}
当前变现情况：{current_monetization or '未变现 / 探索阶段'}
博主目标：{goals or '未明确，请给出推荐方向'}

请严格按 JSON Schema 返回。"""

        data, meta = await self._llm_json(
            system=SYSTEM_PROMPT,
            user=user_msg,
            tier=tier,
            task="reasoning" if tier in {"max", "addon"} else "chat",
            temperature=0.4,
        )
        # 校验
        data["risk_level"] = max(1, min(5, int(data.get("risk_level", 2))))
        data["_meta"] = meta
        return data
