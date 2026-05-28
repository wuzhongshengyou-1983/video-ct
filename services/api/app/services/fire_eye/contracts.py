"""数据契约 — VideoCTContext 统一数据总线"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlatformData:
    """F1 平台数据（TikHub / 开放平台）"""
    play_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    share_count: Optional[int] = None
    completion_rate: Optional[float] = None
    source: Optional[str] = None          # "tikhub" | "official_api" | "mock"
    confidence: float = 0.0


@dataclass
class TechMetadata:
    """F2 技术元数据（FFprobe / 画质评分）"""
    duration_sec: Optional[float] = None
    resolution: Optional[str] = None      # "1920x1080"
    fps: Optional[float] = None
    bitrate_kbps: Optional[int] = None
    quality_score: Optional[float] = None  # Qwen VL 画质评分 0-10


@dataclass
class ContentUnderstanding:
    """F3 AI内容理解（ASR + OCR + LLM摘要）"""
    transcript: Optional[str] = None       # ASR 语音转写
    title_ocr: Optional[str] = None        # 标题OCR
    cover_desc: Optional[str] = None       # Qwen VL 封面描述
    content_summary: Optional[str] = None  # LLM 内容摘要


@dataclass
class CompetitorInsight:
    """F4 趋势竞品（竞品搜索 + LLM知识基准）"""
    track: Optional[str] = None
    benchmark_text: Optional[str] = None   # format_for_prompt 格式化基准文本
    top_creators: list = field(default_factory=list)


@dataclass
class VideoCTContext:
    """统一数据总线 — 贯穿三步 Pipeline 的数据契约"""
    video_url: str = ""
    diagnosis_id: str = ""

    # 各族数据（逐步填充）
    platform: PlatformData = field(default_factory=PlatformData)
    tech: TechMetadata = field(default_factory=TechMetadata)
    content: ContentUnderstanding = field(default_factory=ContentUnderstanding)
    competitor: CompetitorInsight = field(default_factory=CompetitorInsight)

    # 诊断结果（Step 3 输出）
    ct_report: Optional[dict] = None

    # 流水线元信息
    cost_yuan: float = 0.0
    degraded_families: list = field(default_factory=list)  # 降级的族
    errors: list = field(default_factory=list)
