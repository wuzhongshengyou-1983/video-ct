"""人设观察员 Agent · IPP 诊断."""
from __future__ import annotations

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """你是「人设观察员」，根据博主多条视频 + 自述，输出 IPP 人设档案。

【6 维评分】（0-100 分）
1. 标签清晰度
2. 视觉辨识度
3. 语言记忆度
4. 价值定位
5. 情绪基调
6. 用户感知一致性

【12 原型库】
- 气场型：行业权威 / 反差大佬 / 凶猛敢说
- 干货型：教学派 / 拆解派 / 资源派
- 共情型：闺蜜型 / 治愈系 / 共同体
- 趣味型：段子手 / 鬼马少年 / 反差萌

【输出 JSON Schema】
{
  "primary_archetype": "教学派" 等 12 个之一,
  "sub_archetype": null 或 12 个之一,
  "contrast_point": "一句话描述反差点",
  "self_tags": ["标签 1", "标签 2", ...] (≤5),
  "audience_tags": ["从评论池聚类出的粉丝叫法", ...] (≤5),
  "scores": {
    "标签清晰度": int, "视觉辨识度": int, "语言记忆度": int,
    "价值定位": int, "情绪基调": int, "用户感知一致性": int
  },
  "consistency_score": int (6 维加权平均),
  "canvas": {
    "主原型": "...", "反差点": "...", "一句话标签": "...",
    "视觉锚点": "...", "语言锚点": "...", "情绪基调": "...",
    "独有价值": "...", "拒绝清单": "...", "演进方向": "..."
  },
  "diagnosis": {
    "病灶": [{"type": "人设漂移|标签泛化|反差缺失|价值模糊|情绪不稳|自我感知错位", "evidence": "...", "fix": "..."}],
    "suggestions": [{"priority": "P0"|"P1"|"P2", "action": "..."}]
  },
  "drift_alert": false (true 当一致性 < 60)
}

不要 markdown 代码块，直接返回纯 JSON。"""


class PersonaScoutAgent(BaseAgent):
    name = "PersonaScout"
    role = "博主人设 IPP 诊断专家"

    async def run(
        self,
        *,
        videos_summary: str = "",
        comments_summary: str = "",
        user_description: str = "",
        track: str = "通用",
        tier: str = "free",
    ) -> dict:
        user_msg = f"""请为博主做 IPP 人设诊断：

【博主自述】
{user_description or '(未提供)'}

【博主最近视频摘要】
{videos_summary or '(无)'}

【评论池摘要（粉丝叫法、高频疑问、情绪极性）】
{comments_summary or '(无)'}

【细分赛道】
{track}

请严格返回 JSON。"""

        data, meta = await self._llm_json(
            system=SYSTEM_PROMPT,
            user=user_msg,
            tier=tier,
            temperature=0.3,
        )
        # 校验
        scores = data.get("scores", {})
        for k in ["标签清晰度", "视觉辨识度", "语言记忆度", "价值定位", "情绪基调", "用户感知一致性"]:
            scores[k] = max(0, min(100, int(scores.get(k, 60))))
        data["scores"] = scores
        data["consistency_score"] = max(0, min(100, int(data.get("consistency_score", 60))))
        data["drift_alert"] = data["consistency_score"] < 60
        data["_meta"] = meta
        return data
