"""内容生成手 Agent · 钩子/标题/封面/脚本."""
from __future__ import annotations

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """你是「内容生成手」，专门为短视频博主生成爆款级钩子、标题、封面文案。

【输出 JSON Schema】
{
  "hooks": [{"text": "...", "type": "痛点提问|反转剧情|劲爆观点", "score": 0-100}] (5 条),
  "titles": [{"text": "...", "platform": "douyin|kuaishou|xiaohongshu", "score": 0-100}] (5 条),
  "cover_texts": [{"main": "...", "sub": "...", "tone": "震撼|好奇|温暖|权威"}] (3 条),
  "recommended_hook_index": int 0-4,
  "recommended_title_index": int 0-4
}

不要 markdown，直接 JSON。每条不超过 30 字。"""


class ContentMakerAgent(BaseAgent):
    name = "ContentMaker"
    role = "爆款短视频内容创作专家"

    async def run(
        self,
        *,
        topic: str,
        track: str = "通用",
        persona_archetype: str | None = None,
        tier: str = "free",
    ) -> dict:
        user_msg = f"""请为以下选题生成钩子/标题/封面：

选题：{topic}
赛道：{track}
博主人设原型：{persona_archetype or '通用'}
"""
        data, meta = await self._llm_json(
            system=SYSTEM_PROMPT, user=user_msg, tier=tier, temperature=0.7
        )
        data["_meta"] = meta
        return data
