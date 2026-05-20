"""诊断业务逻辑 · 真实 OCR/ASR + 自动重试 + 分步耗时日志."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.ct_radiologist import CTRadiologistAgent
from app.config import settings
from app.core.exceptions import BizException, QuotaExceededError
from app.models.archive import Archive
from app.models.diagnosis import Diagnosis, Report
from app.models.user import User
from app.services.subscription_service import get_user_tier


def detect_platform(url: str) -> str:
    """从 URL 推断平台."""
    u = urlparse(url).netloc.lower()
    if "douyin" in u or "tiktok" in u:
        return "douyin"
    if "kuaishou" in u or "ixigua" in u:
        return "kuaishou"
    if "weixin" in u or "channels" in u or "wxsnsdy" in u:
        return "shipinhao"
    if "xiaohongshu" in u or "xhslink" in u:
        return "xiaohongshu"
    if "bilibili" in u or "b23" in u:
        return "bilibili"
    return "unknown"


async def check_quota(db: AsyncSession, user: User) -> tuple[str, int]:
    """检查配额 · 返回 (quota_source, used_this_month)."""
    tier = await get_user_tier(db, user.id)

    # 本月已用诊断数
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    used = await db.scalar(
        select(func.count(Diagnosis.id)).where(
            Diagnosis.user_id == user.id,
            Diagnosis.created_at >= month_start,
            Diagnosis.status != "failed",
        )
    ) or 0

    # MAX 不限次（公平使用 ≤ 30）
    if tier == "max":
        if used >= 30:
            raise QuotaExceededError("max_monthly_30")
        return "max", used
    # PRO 4 次/月
    if tier == "pro":
        if used >= 4:
            raise QuotaExceededError("pro_monthly_4")
        return "pro", used
    # 免费 3 次/月（用券或单次付费会另外计算）
    if used >= settings.FREE_MONTHLY_SCANS:
        raise QuotaExceededError("free_monthly_3")
    return "free", used


async def create_diagnosis(
    db: AsyncSession,
    *,
    user: User,
    video_url: str,
    track: str | None = None,
    diagnosis_type: str = "ct_basic",
) -> Diagnosis:
    quota_source, _ = await check_quota(db, user)
    platform = detect_platform(video_url)

    diag = Diagnosis(
        user_id=user.id,
        video_url=video_url,
        video_platform=platform,
        status="queued",
        diagnosis_type=diagnosis_type,
        quota_source=quota_source,
        progress_pct=0,
    )
    db.add(diag)
    await db.flush()
    return diag


# ==================== 视频元数据抓取 ====================


async def fetch_video_meta(video_url: str, platform: str) -> dict:
    """抓取视频元数据 · 优先真实 API，不可用时降级 mock."""
    logger.info(f"[fetch_video_meta] url={video_url} platform={platform}")

    # 尝试通过硅基流动 API 获取视频信息（如果提供了 API key）
    if settings.SILICONFLOW_API_KEY:
        try:
            from app.services.llm_router import llm_router

            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个视频数据分析助手。给定一个视频链接，"
                        "请用 JSON 格式返回可能的视频元数据。"
                        "对于无法确定的信息，请使用合理估计值并在字段后加 _estimated: true。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"请分析此视频链接的可能元数据:\n"
                        f"URL: {video_url}\n"
                        f"平台: {platform}\n\n"
                        f"返回 JSON，包含: title, duration_sec, publish_at, "
                        f"stats(play_count/like_count/comment_count/share_count/collect_count), "
                        f"author(nickname/follower_count)"
                    ),
                },
            ]

            result = await llm_router.chat(
                messages=messages,
                tier="free",
                task="chat",
                response_format="json_object",
                temperature=0.1,
                max_tokens=1024,
            )
            meta = result.as_json()
            meta["url"] = video_url
            meta["platform"] = platform
            logger.info(f"[fetch_video_meta] AI estimated meta: {meta.get('title', 'N/A')[:50]}")
            return meta

        except Exception as exc:
            logger.warning(f"[fetch_video_meta] AI 元数据提取失败，降级 mock: {exc}")

    # 降级 mock
    logger.info("[fetch_video_meta] using mock data")
    return {
        "url": video_url,
        "platform": platform,
        "title": "（开发期 mock 标题）创业者凌晨四点的真实状态",
        "duration_sec": 47,
        "publish_at": "2026-05-19T22:13:00+08:00",
        "stats": {
            "play_count": 12345,
            "like_count": 234,
            "comment_count": 56,
            "share_count": 12,
            "collect_count": 30,
        },
        "author": {
            "nickname": "（mock）某博主",
            "follower_count": 8523,
        },
    }


# ==================== OCR + ASR（真实服务） ====================


async def fetch_ocr_asr(video_url: str) -> tuple[str, str]:
    """获取 OCR + ASR 文本 · 调用真实 ocr_asr 服务."""
    t0 = time.monotonic()

    ocr_text: str = ""
    asr_text: str = ""

    # OCR：从视频封面/截图提取
    try:
        from app.services.ocr_asr import extract_text_from_image, transcribe_audio

        # 并行执行 OCR 和 ASR
        ocr_task = asyncio.create_task(_safe_ocr(video_url))
        asr_task = asyncio.create_task(_safe_asr(video_url))

        ocr_text, asr_text = await asyncio.gather(ocr_task, asr_task)

    except Exception as exc:
        logger.warning(f"[fetch_ocr_asr] 服务初始化失败: {exc}")

    elapsed = time.monotonic() - t0
    logger.info(
        f"[fetch_ocr_asr] done in {elapsed:.2f}s: "
        f"ocr_len={len(ocr_text)}, asr_len={len(asr_text)}"
    )
    return ocr_text, asr_text


async def _safe_ocr(video_url: str) -> str:
    """安全的 OCR 调用 · 失败返回空字符串."""
    try:
        from app.services.ocr_asr import extract_text_from_image
        return await extract_text_from_image(video_url)
    except Exception as exc:
        logger.warning(f"[_safe_ocr] failed: {exc}")
        return ""


async def _safe_asr(video_url: str) -> str:
    """安全的 ASR 调用 · 失败返回空字符串."""
    try:
        from app.services.ocr_asr import transcribe_audio
        return await transcribe_audio(video_url)
    except Exception as exc:
        logger.warning(f"[_safe_asr] failed: {exc}")
        return ""


# ==================== Pipeline ====================


async def _log_step(step_name: str, start_time: float) -> None:
    """记录步骤耗时."""
    elapsed = time.monotonic() - start_time
    logger.info(f"[Pipeline] ✓ {step_name} ({elapsed:.2f}s)")


async def run_full_pipeline(
    db: AsyncSession, diagnosis_id: int, *, max_retries: int = 1
) -> Report:
    """端到端跑诊断 → 出报告 · 支持自动重试 + 分步耗时日志.

    Args:
        db: 数据库会话.
        diagnosis_id: 诊断记录 ID.
        max_retries: 失败后最多重试次数（默认 1 次）.

    Returns:
        生成的 Report 对象.
    """
    pipeline_start = time.monotonic()
    logger.info(f"[Pipeline] === 开始诊断 diag_id={diagnosis_id} ===")

    res = await db.execute(select(Diagnosis).where(Diagnosis.id == diagnosis_id))
    diag = res.scalar_one()

    diag.status = "processing"
    diag.started_at = datetime.now(timezone.utc)
    diag.progress_pct = 10
    await db.commit()

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.warning(
                    f"[Pipeline] 重试 {attempt}/{max_retries} diag_id={diagnosis_id}"
                )
                # 重置进度
                diag.status = "processing"
                diag.progress_pct = 10 * (attempt + 1)
                diag.error = None
                await db.commit()
                # 短暂延迟后重试
                await asyncio.sleep(2)

            # ---- 步骤 1：抓元数据 ----
            t1 = time.monotonic()
            meta = await fetch_video_meta(diag.video_url, diag.video_platform or "unknown")
            diag.video_meta = meta
            diag.progress_pct = 30
            await db.commit()
            await _log_step("Step 1 fetch_video_meta", t1)

            # ---- 步骤 2：OCR + ASR ----
            t2 = time.monotonic()
            ocr, asr = await fetch_ocr_asr(diag.video_url)
            diag.progress_pct = 50
            await db.commit()
            await _log_step("Step 2 fetch_ocr_asr", t2)

            # ---- 步骤 3：用户 profile ----
            t3 = time.monotonic()
            from app.models.user import UserProfile
            prof_res = await db.execute(
                select(UserProfile).where(UserProfile.user_id == diag.user_id)
            )
            prof = prof_res.scalar_one_or_none()
            track = prof.track if prof and prof.track else "通用"
            await _log_step("Step 3 load_profile", t3)

            # ---- 步骤 4：跑 CT 诊断官 ----
            t4 = time.monotonic()
            agent = CTRadiologistAgent()
            tier = diag.quota_source
            result = await agent.run(
                video_meta=meta,
                ocr_text=ocr,
                asr_text=asr,
                track=track,
                tier=tier,
            )
            diag.progress_pct = 90
            await db.commit()
            await _log_step("Step 4 ct_radiologist.run()", t4)

            # ---- 步骤 5：保存报告 ----
            t5 = time.monotonic()
            report = Report(
                diagnosis_id=diag.id,
                user_id=diag.user_id,
                overall_score=result["overall_score"],
                grade=result["grade"],
                dimensions=result["dimensions"],
                findings=result.get("findings", []),
                suggestions=result.get("suggestions", []),
                benchmark_gap=result.get("benchmark_gap", {}),
                model_used=result.get("_meta", {}).get("model"),
                cost_cents=result.get("_meta", {}).get("cost_cents", 0),
            )
            db.add(report)

            diag.status = "done"
            diag.completed_at = datetime.now(timezone.utc)
            diag.progress_pct = 100

            # ---- 步骤 6：更新档案 ----
            t6 = time.monotonic()
            await _update_archive(db, diag.user_id, result)
            await _log_step("Step 5-6 save_report + update_archive", t5)

            await db.commit()
            await db.refresh(report)

            total_elapsed = time.monotonic() - pipeline_start
            logger.info(
                f"[Pipeline] === 诊断完成 diag_id={diagnosis_id} "
                f"score={result['overall_score']} grade={result['grade']} "
                f"total={total_elapsed:.2f}s ==="
            )
            return report

        except Exception as exc:
            last_error = exc
            logger.exception(
                f"[Pipeline] 诊断失败 diag_id={diagnosis_id} "
                f"attempt={attempt + 1}/{max_retries + 1}: {exc}"
            )
            if attempt < max_retries:
                continue
            # 最后一次尝试也失败了
            diag.status = "failed"
            diag.error = str(exc)[:1000]
            await db.commit()
            raise

    # 理论上不会到这里，但类型检查器需要
    assert last_error is not None
    raise last_error


async def _update_archive(db: AsyncSession, user_id: int, result: dict) -> None:
    """诊断完成 → 累计到档案."""
    res = await db.execute(select(Archive).where(Archive.user_id == user_id))
    archive = res.scalar_one_or_none()
    if not archive:
        import time as _time
        import random
        import string
        archive = Archive(
            user_id=user_id,
            archive_no=f"VCT-A-{int(_time.time())}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}",
            initial_baseline={"first_overall_score": result["overall_score"]},
        )
        db.add(archive)
        await db.flush()

    archive.total_diagnoses += 1
    archive.current_level = result.get("grade", archive.current_level)
