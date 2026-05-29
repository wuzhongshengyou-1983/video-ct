"""爆火 DNA 分析服务 · Sprint2 核心功能.

分析竞品博主的爆火 DNA，返回 7 维评分 + F-Frame + 策略建议。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

from loguru import logger

from app.services.llm_router import llm_router


@dataclass
class ViralDnaResult:
    """爆火 DNA 分析结果."""
    competitor_nickname: str
    competitor_follower_count: int
    viral_score: float                       # 0-100
    dimensions: list[dict]                   # [{name, score, weight, evidence}] x7
    top_factors: list[dict]                  # [{name, contribution_pct, evidence}] x3
    fframe: list[dict]                       # [{range, label, score, tactic}] x5
    can_copy: list[str]                      # 3 条
    avoid: list[str]                         # 2 条
    transform: list[str]                     # 2 条
    source: str = "llm_analysis"

    def to_dict(self) -> dict:
        return asdict(self)


# ── 7 维默认权重（Sprint2 规范值）──
DIMENSION_WEIGHTS: list[dict[str, Any]] = [
    {"name": "钩子力",   "weight": 0.20},
    {"name": "内容密度", "weight": 0.18},
    {"name": "信任建立", "weight": 0.15},
    {"name": "算法适配", "weight": 0.15},
    {"name": "情绪共鸣", "weight": 0.12},
    {"name": "叙事结构", "weight": 0.12},
    {"name": "变现引导", "weight": 0.08},
]

# F-Frame 时间轴 5 段默认标签
FFRAME_DEFAULTS: list[dict[str, Any]] = [
    {"range": "0-3s",   "label": "钩子"},
    {"range": "3-8s",   "label": "密度"},
    {"range": "8-20s",  "label": "转折"},
    {"range": "20-45s", "label": "高潮"},
    {"range": "结尾",   "label": "CTA"},
]


def _fallback_result(
    competitor_nickname: str,
    track: str,
    competitor_follower_count: int = 0,
) -> ViralDnaResult:
    """LLM 调用失败时的兜底模板."""
    dimensions = [
        {
            "name": d["name"],
            "score": 70,
            "weight": d["weight"],
            "evidence": f"{competitor_nickname} 在该维度的数据暂无法获取，建议人工复核。",
        }
        for d in DIMENSION_WEIGHTS
    ]
    viral_score = round(sum(dim["score"] * dim["weight"] for dim in dimensions), 1)
    return ViralDnaResult(
        competitor_nickname=competitor_nickname,
        competitor_follower_count=competitor_follower_count,
        viral_score=viral_score,
        dimensions=dimensions,
        top_factors=[
            {
                "name": "钩子力",
                "contribution_pct": 28,
                "evidence": "分析服务暂时不可用，此为默认示例数据，请稍后重试。",
            }
        ],
        fframe=[
            {**seg, "score": 70, "tactic": "（暂无分析）"}
            for seg in FFRAME_DEFAULTS
        ],
        can_copy=["（分析暂时不可用）"],
        avoid=["（分析暂时不可用）"],
        transform=["（分析暂时不可用）"],
        source="fallback",
    )


def _build_prompt(
    competitor_nickname: str,
    track: str,
    diagnosis_summary: str | None,
) -> str:
    ctx_section = (
        f"\n【用户诊断摘要】\n{diagnosis_summary}\n"
        if diagnosis_summary
        else ""
    )
    return f"""你是一名短视频爆款研究专家，擅长拆解 TikTok / 抖音 / 小红书头部账号的爆火规律。

请分析以下竞品账号的爆火 DNA，并返回严格符合格式的 JSON。

【账号昵称】{competitor_nickname}
【赛道】{track}{ctx_section}

请从以下 7 个维度打分（0-100），并给出具体证据（每条 20 字以内）：
1. 钩子力（权重 0.22）：开头 3 秒留人能力
2. 内容密度（权重 0.18）：信息/价值密度
3. 信任建立（权重 0.16）：专业感、人设可信度
4. 算法适配（权重 0.16）：标签、时长、发布节奏
5. 情绪共鸣（权重 0.14）：引发强烈情绪反应
6. 叙事结构（权重 0.08）：故事/逻辑完整度
7. 变现引导（权重 0.06）：引流/带货/涨粉能力

同时给出：
- top_factors：贡献最大的 3 个因子（name, contribution_pct, evidence）
- fframe：F-Frame 时间轴 5 段（range, label, score, tactic）
  段落固定为：0-3s(钩子) / 3-8s(密度) / 8-20s(转折) / 20-45s(高潮) / 结尾(CTA)
- can_copy：你能直接参考复用的 2-3 条策略
- avoid：不建议照搬的 1-2 条（配合说明原因）
- transform：改造建议 1-2 条

返回纯 JSON，不要任何 markdown 包装，格式如下：
{{
  "dimensions": [
    {{"name": "钩子力", "score": 85, "weight": 0.22, "evidence": "..."}},
    {{"name": "内容密度", "score": 72, "weight": 0.18, "evidence": "..."}},
    {{"name": "信任建立", "score": 68, "weight": 0.16, "evidence": "..."}},
    {{"name": "算法适配", "score": 81, "weight": 0.16, "evidence": "..."}},
    {{"name": "情绪共鸣", "score": 75, "weight": 0.14, "evidence": "..."}},
    {{"name": "叙事结构", "score": 70, "weight": 0.08, "evidence": "..."}},
    {{"name": "变现引导", "score": 65, "weight": 0.06, "evidence": "..."}}
  ],
  "top_factors": [
    {{"name": "钩子力", "contribution_pct": 28, "evidence": "..."}}
  ],
  "fframe": [
    {{"range": "0-3s", "label": "钩子", "score": 91, "tactic": "数字承诺+悬念"}},
    {{"range": "3-8s", "label": "密度", "score": 78, "tactic": "6cut/s 快剪"}},
    {{"range": "8-20s", "label": "转折", "score": 85, "tactic": "反差对比"}},
    {{"range": "20-45s", "label": "高潮", "score": 88, "tactic": "极限演示"}},
    {{"range": "结尾", "label": "CTA", "score": 82, "tactic": "短路径引导"}}
  ],
  "can_copy": ["开头数字承诺句式", "快剪节奏"],
  "avoid": ["需要大量素材支撑"],
  "transform": ["把极限演示改为对比演示"]
}}"""


def _parse_llm_result(
    raw: dict,
    competitor_nickname: str,
    track: str,
    competitor_follower_count: int = 0,
) -> ViralDnaResult:
    """解析并校验 LLM 返回的 dict，填补缺失字段."""
    # 校验 dimensions
    dims = raw.get("dimensions", [])
    if not isinstance(dims, list) or len(dims) != 7:
        logger.warning("[ViralDNA] dimensions 格式异常，使用 fallback")
        return _fallback_result(competitor_nickname, track, competitor_follower_count)

    # 规范化每个维度，确保 weight 使用系统权重（LLM 可能乱填）
    weight_map = {d["name"]: d["weight"] for d in DIMENSION_WEIGHTS}
    dimensions: list[dict] = []
    for dim in dims:
        name = str(dim.get("name", ""))
        score = max(0, min(100, int(dim.get("score", 70))))
        weight = weight_map.get(name, dim.get("weight", 0.1))
        evidence = str(dim.get("evidence", ""))
        dimensions.append({"name": name, "score": score, "weight": weight, "evidence": evidence})

    # 计算综合分
    viral_score = round(sum(d["score"] * d["weight"] for d in dimensions), 1)

    # top_factors
    top_factors = raw.get("top_factors", [])
    if not isinstance(top_factors, list) or not top_factors:
        # 自动按贡献（score * weight）取 top3
        sorted_dims = sorted(dimensions, key=lambda d: d["score"] * d["weight"], reverse=True)
        total_contribution = sum(d["score"] * d["weight"] for d in dimensions) or 1
        top_factors = [
            {
                "name": d["name"],
                "contribution_pct": round(d["score"] * d["weight"] / total_contribution * 100),
                "evidence": d["evidence"],
            }
            for d in sorted_dims[:3]
        ]

    # fframe
    fframe = raw.get("fframe", [])
    if not isinstance(fframe, list) or len(fframe) != 5:
        fframe = [{**seg, "score": 70, "tactic": "（暂无分析）"} for seg in FFRAME_DEFAULTS]

    return ViralDnaResult(
        competitor_nickname=competitor_nickname,
        competitor_follower_count=competitor_follower_count,
        viral_score=viral_score,
        dimensions=dimensions,
        top_factors=top_factors[:3],
        fframe=fframe,
        can_copy=raw.get("can_copy", []),
        avoid=raw.get("avoid", []),
        transform=raw.get("transform", []),
        source="llm_analysis",
    )


async def analyze_viral_dna(
    competitor_nickname: str,
    track: str,
    competitor_follower_count: int = 0,
    sample_video_url: str | None = None,
    diagnosis_summary: str | None = None,
) -> ViralDnaResult:
    """分析竞品博主的爆火 DNA，返回 7 维评分 + F-Frame + 策略建议.

    Args:
        competitor_nickname: 竞品博主昵称
        track: 赛道名称
        competitor_follower_count: 竞品粉丝数（来自 Benchmark 表）
        sample_video_url: 可选，代表性视频 URL（暂用于未来 TikHub 扩展）
        diagnosis_summary: 可选，用户自己的诊断摘要，用于生成更有针对性的策略

    Returns:
        ViralDnaResult dataclass（含 viral_score / dimensions / fframe / can_copy / avoid / transform）
    """
    prompt = _build_prompt(competitor_nickname, track, diagnosis_summary)
    messages = [
        {
            "role": "system",
            "content": "你是一名短视频爆款研究专家。请只输出纯 JSON，不加任何 markdown 格式。",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        resp = await llm_router.chat(
            messages=messages,
            tier="free",
            task="chat",
            response_format="json_object",
            temperature=0.3,
            max_tokens=2048,
        )
        raw = resp.as_json()
        return _parse_llm_result(raw, competitor_nickname, track, competitor_follower_count)
    except Exception as exc:
        logger.warning(
            f"[ViralDNA] LLM 调用失败，降级 fallback: competitor={competitor_nickname} "
            f"track={track} err={exc}"
        )
        return _fallback_result(competitor_nickname, track, competitor_follower_count)
