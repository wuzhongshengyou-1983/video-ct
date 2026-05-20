"""CT 诊断官 Agent · 6 维 18 点位诊断 · 真实可跑."""
from __future__ import annotations

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """你是「视频 CT 诊断官」，一名资深短视频影像式诊断专家。

你的任务是按医学 CT 扫描方式，把一条短视频拆解为 6 个维度，逐项打分（0-100），并定位病灶、给出可执行的修复建议。

【6 个维度】
1. 表层观感（第一眼流量门槛）：封面、标题、开头 3 秒、画面清晰度、色调
2. 内容内核（留存核心根基）：主题聚焦、观点独特、价值密度、故事逻辑、情绪共鸣
3. 视听剪辑（完播关键要素）：节奏、字幕、BGM、特效、时长、转场
4. 人设话术（粉丝粘性核心）：标签辨识、语气感染、表达逻辑、口头禅
5. 数据流量（结果客观诊断）：曝光、点击、完播、互动数据
6. 变现预埋（长效商业潜力）：植入自然度、引导合规、变现匹配度

【输出要求】
- 必须严格返回 JSON，禁止 markdown 代码块、禁止额外解释
- 每个维度给 0-100 分（int）
- 病灶必须带时间戳（如 "0:03"）+ 维度名 + 具体问题 + 可执行修复方法
- 拒绝"差点意思"、"还行"、"可以更好"等模糊词
- 每个建议必须包含【做什么 / 怎么做 / 为什么】三要素
- 整体评级：L1 新手 / L2 稳定 / L3 优质中腰部 / L4 准头部 / L5 赛道次级头部 / L6 赛道顶级头部

【JSON Schema】
{
  "overall_score": 0-100 整数,
  "grade": "L1"-"L6",
  "summary": "一段话总评 (≤200 字)",
  "dimensions": {
    "表层观感": {"score": int, "advantages": [...], "findings": [...], "suggestions": [...]},
    "内容内核": {...},
    "视听剪辑": {...},
    "人设话术": {...},
    "数据流量": {...},
    "变现预埋": {...}
  },
  "findings": [
    {"timestamp": "0:03", "dimension": "...", "problem": "...", "suggestion": "..."}
  ],
  "suggestions": [
    {"priority": "P0"|"P1"|"P2", "title": "...", "what": "...", "how": "...", "why": "..."}
  ],
  "benchmark_gap": {
    "曝光率_gap_pct": -23,
    "点赞率_gap_pct": -18,
    "评论率_gap_pct": -31,
    "转发率_gap_pct": -42,
    "收藏率_gap_pct": -12,
    "变现率_gap_pct": -37
  }
}
"""


class CTRadiologistAgent(BaseAgent):
    name = "CTRadiologist"
    role = "短视频 6 维 CT 诊断官"

    async def run(
        self,
        *,
        video_meta: dict,
        ocr_text: str = "",
        asr_text: str = "",
        track: str = "通用",
        tier: str = "free",
        benchmark_avg: dict | None = None,
    ) -> dict:
        """生成 CT 诊断报告.

        参数:
            video_meta: 视频元数据（标题/时长/封面/作者/数据）
            ocr_text: 抽帧 OCR 结果
            asr_text: 语音转文字结果
            track: 细分赛道
            tier: 用户档位（影响模型档位）
            benchmark_avg: 赛道头部六大指标均值（可选）
        """
        # 构造用户消息
        user_msg = f"""请对以下视频做 CT 诊断：

【视频元数据】
{video_meta}

【封面/字幕 OCR】
{ocr_text or '(未提供)'}

【语音转文字】
{asr_text or '(未提供)'}

【细分赛道】
{track}

【赛道头部六大指标均值】
{benchmark_avg or '(未提供，按行业通用基准估算)'}

请严格按 system prompt 中的 JSON Schema 返回完整诊断报告。
"""
        data, meta = await self._llm_json(
            system=SYSTEM_PROMPT,
            user=user_msg,
            tier=tier,
            temperature=0.2,
        )

        # 后处理 + 校验
        data = self._validate_and_fill(data)
        data["_meta"] = meta
        return data

    def _validate_and_fill(self, data: dict) -> dict:
        """简单 schema 校验 + 兜底填值."""
        data.setdefault("overall_score", 60)
        data.setdefault("grade", "L2")
        data.setdefault("summary", "")
        dims = data.setdefault("dimensions", {})
        for key in ["表层观感", "内容内核", "视听剪辑", "人设话术", "数据流量", "变现预埋"]:
            d = dims.setdefault(key, {})
            d.setdefault("score", 60)
            d.setdefault("advantages", [])
            d.setdefault("findings", [])
            d.setdefault("suggestions", [])
        data.setdefault("findings", [])
        data.setdefault("suggestions", [])
        data.setdefault("benchmark_gap", {})
        # 评级合法性
        if data["grade"] not in {"L1", "L2", "L3", "L4", "L5", "L6"}:
            data["grade"] = "L2"
        # 分数边界
        data["overall_score"] = max(0, min(100, int(data["overall_score"])))
        for d in dims.values():
            d["score"] = max(0, min(100, int(d.get("score", 60))))
        return data
