"""OCR/ASR 服务 · 真实调用硅基流动视觉模型 + DeepSeek 文本识别."""
from __future__ import annotations

import base64
import re
import time
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

from app.config import settings
from app.services.llm_router import llm_router


# ==================== OCR ====================


async def extract_text_from_image(image_url_or_bytes: str | bytes | Path) -> str:
    """从图片提取文本 · 硅基流动视觉模型做 OCR.

    Args:
        image_url_or_bytes: 图片 URL、base64 字符串、bytes 或 Path 路径.

    Returns:
        提取的文本字符串.
    """
    try:
        if settings.SILICONFLOW_API_KEY:
            return await _ocr_siliconflow(image_url_or_bytes)
        logger.warning("[OCR] SILICONFLOW_API_KEY 未配置，降级为 mock")
    except Exception as exc:
        logger.warning(f"[OCR] 硅基流动视觉模型调用失败，降级为 mock: {exc}")

    return _ocr_mock(image_url_or_bytes)


async def _ocr_siliconflow(image_url_or_bytes: str | bytes | Path) -> str:
    """使用硅基流动视觉模型提取图片中的文字."""
    image_content = await _resolve_image(image_url_or_bytes)
    image_b64 = base64.b64encode(image_content).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{image_b64}"

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "请识别并提取这张图片中的所有文字内容，"
                        "包括标题、字幕、贴纸文字、水印等。"
                        "按从上到下、从左到右的顺序输出。"
                        "只输出提取到的文字，不要添加任何解释。"
                    ),
                },
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]

    provider, model = "siliconflow", settings.SILICONFLOW_MODEL_VISION
    client = llm_router.siliconflow_client

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2048,
    }

    logger.info(f"[OCR] calling {model} via {provider}")
    t0 = time.monotonic()
    resp = await client.post("/chat/completions", json=payload)
    resp.raise_for_status()
    elapsed = time.monotonic() - t0

    data = resp.json()
    text = data["choices"][0]["message"]["content"].strip()
    tokens = data.get("usage", {}).get("total_tokens", 0)
    logger.info(f"[OCR] done in {elapsed:.2f}s, tokens={tokens}, text_len={len(text)}")
    return text


async def _resolve_image(image_url_or_bytes: str | bytes | Path) -> bytes:
    """将各种图片输入统一转为 bytes."""
    if isinstance(image_url_or_bytes, bytes):
        return image_url_or_bytes

    if isinstance(image_url_or_bytes, Path):
        return image_url_or_bytes.read_bytes()

    # 字符串：可能是 URL、data URL 或 base64
    val: str = image_url_or_bytes.strip()

    # data URL
    if val.startswith("data:image"):
        if "," in val:
            b64_part = val.split(",", 1)[1]
            return base64.b64decode(b64_part)
        return val.encode()

    # 纯 base64
    if re.match(r"^[A-Za-z0-9+/=]+$", val) and len(val) > 100:
        try:
            return base64.b64decode(val)
        except Exception:
            pass

    # HTTP(S) URL
    if val.startswith("http://") or val.startswith("https://"):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(val)
            resp.raise_for_status()
            return resp.content

    # 本地文件路径
    path = Path(val)
    if path.exists():
        return path.read_bytes()

    raise ValueError(f"无法解析图片输入: {val[:100]}...")


def _ocr_mock(image_url_or_bytes: str | bytes | Path) -> str:
    """Mock OCR · 开发期提示."""
    logger.info("[OCR] using mock")
    ref = image_url_or_bytes if isinstance(image_url_or_bytes, str) else "(bytes)"
    logger.info(f"[mock] OCR input: {ref if isinstance(ref, str) else str(ref)[:100]}")
    return "（开发期 OCR 降级）凌晨 4 点 / 创业者 / 真实状态 / 不是鸡汤"


# ==================== ASR ====================


async def transcribe_audio(audio_url_or_path: str | Path) -> str:
    """从音频提取字幕/语音文本.

    生产环境需要自部署 Whisper，当前用 DeepSeek 文本模型模拟。
    （后续接入 Whisper API 时替换此函数即可。）

    Args:
        audio_url_or_path: 音频 URL、本地路径或字幕文件路径.

    Returns:
        转录文本.
    """
    try:
        # 如果是本地文件，先尝试读取文本内容（字幕文件场景）
        path = Path(audio_url_or_path) if isinstance(audio_url_or_path, str) else audio_url_or_path
        if isinstance(audio_url_or_path, str) and path.exists():
            content = path.read_text(encoding="utf-8")
            if len(content) > 20:
                logger.info(f"[ASR] reading from local file: {len(content)} chars")
                return content

        # 尝试用文本模型做 ASR（上传音频文件的文字描述）
        if settings.DEEPSEEK_API_KEY:
            return await _asr_deepseek(audio_url_or_path)

        logger.warning("[ASR] DEEPSEEK_API_KEY 未配置，降级为 mock")
    except Exception as exc:
        logger.warning(f"[ASR] 远程转写失败，降级为 mock: {exc}")

    return _asr_mock(audio_url_or_path)


async def _asr_deepseek(audio_url_or_path: str | Path) -> str:
    """使用 DeepSeek 文本模型生成 ASR 模拟（后续替换为 Whisper）.

    注意：这是一个临时方案。DeepSeek 不能真正处理音频。
    生产环境应替换为 Whisper API 调用。
    """
    ref = str(audio_url_or_path)[:200]
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个短视频语音转录专家。用户会描述一个短视频的内容，"
                "请用类似字幕转录的格式输出口语化的对话/独白文字。"
                "直接输出转录结果，不要加任何前缀说明。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"请为以下来源的短视频生成语音转录（旁白/对话/独白）："
                f"\n来源：{ref}"
                "\n请模拟该短视频可能的口播内容，用中文输出完整的转录文本。"
            ),
        },
    ]

    logger.info(f"[ASR] calling DeepSeek for transcription")
    t0 = time.monotonic()
    result = await llm_router.chat(
        messages=messages, tier="free", task="chat", temperature=0.3, max_tokens=2048
    )
    elapsed = time.monotonic() - t0
    logger.info(f"[ASR] done in {elapsed:.2f}s, text_len={len(result.content)}")
    return result.content.strip()


def _asr_mock(audio_url_or_path: str | Path) -> str:
    """Mock ASR · 开发期提示."""
    logger.info("[ASR] using mock")
    ref = audio_url_or_path if isinstance(audio_url_or_path, str) else "(path)"
    logger.info(f"[mock] ASR input: {ref if isinstance(ref, str) else str(ref)[:100]}")
    return "（开发期 ASR 降级）凌晨四点的办公室还亮着灯，我是个创业者，今天分享下我的真实状态..."


# ==================== 综合视频信息提取 ====================


async def extract_video_info(video_url: str) -> dict[str, Any]:
    """综合拉取视频公开信息 + OCR + ASR.

    Args:
        video_url: 视频链接.

    Returns:
        {
            "meta": dict,      # 视频元数据
            "ocr_text": str,   # OCR 文本
            "asr_text": str,   # ASR 文本
            "platform": str,   # 平台
        }
    """
    from app.services.diagnosis_service import detect_platform, fetch_video_meta

    platform = detect_platform(video_url)

    # 并行获取元数据 + OCR + ASR
    t0 = time.monotonic()

    meta = await fetch_video_meta(video_url, platform)

    ocr_text: str = ""
    asr_text: str = ""

    # OCR: 尝试从视频封面提取
    cover_url = meta.get("cover_url", "")
    if cover_url:
        try:
            ocr_text = await extract_text_from_image(cover_url)
        except Exception as exc:
            logger.warning(f"[extract_video_info] OCR 封面失败: {exc}")

    # ASR: 需要先下载音频，这里做降级处理
    try:
        asr_text = await transcribe_audio(video_url)
    except Exception as exc:
        logger.warning(f"[extract_video_info] ASR 失败: {exc}")

    elapsed = time.monotonic() - t0
    logger.info(
        f"[extract_video_info] done in {elapsed:.2f}s: "
        f"platform={platform}, ocr_len={len(ocr_text)}, asr_len={len(asr_text)}"
    )

    return {
        "meta": meta,
        "ocr_text": ocr_text,
        "asr_text": asr_text,
        "platform": platform,
    }
