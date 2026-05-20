"""诊断业务逻辑."""
from __future__ import annotations

import re
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


# Mock 视频元数据抓取（生产应调真实平台 API 或合规爬虫）
async def fetch_video_meta(video_url: str, platform: str) -> dict:
    """Mock 视频元数据 · 实际项目应对接平台 OAuth/数据商."""
    logger.info(f"[mock] fetch_video_meta url={video_url} platform={platform}")
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


async def fetch_ocr_asr(video_url: str) -> tuple[str, str]:
    """Mock OCR/ASR · 实际项目应跑 PaddleOCR + Whisper."""
    logger.info(f"[mock] fetch_ocr_asr url={video_url}")
    return (
        "（mock OCR）凌晨 4 点 / 创业者 / 真实状态 / 不是鸡汤",
        "（mock ASR）凌晨四点的办公室还亮着灯，我是个创业者，今天分享下我的真实状态...",
    )


async def run_full_pipeline(db: AsyncSession, diagnosis_id: int) -> Report:
    """端到端跑诊断 → 出报告 · 适合 Celery 后台任务."""
    res = await db.execute(select(Diagnosis).where(Diagnosis.id == diagnosis_id))
    diag = res.scalar_one()

    diag.status = "processing"
    diag.started_at = datetime.now(timezone.utc)
    diag.progress_pct = 10
    await db.commit()

    try:
        # 1. 抓元数据
        meta = await fetch_video_meta(diag.video_url, diag.video_platform or "unknown")
        diag.video_meta = meta
        diag.progress_pct = 30
        await db.commit()

        # 2. OCR + ASR
        ocr, asr = await fetch_ocr_asr(diag.video_url)
        diag.progress_pct = 50
        await db.commit()

        # 3. 用户 profile
        from app.models.user import UserProfile
        prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == diag.user_id))
        prof = prof_res.scalar_one_or_none()
        track = prof.track if prof and prof.track else "通用"

        # 4. 跑 CT 诊断官
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

        # 5. 保存报告
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

        # 6. 更新档案
        await _update_archive(db, diag.user_id, result)

        await db.commit()
        await db.refresh(report)
        return report

    except Exception as exc:
        logger.exception(f"诊断失败 diag_id={diagnosis_id}: {exc}")
        diag.status = "failed"
        diag.error = str(exc)[:1000]
        await db.commit()
        raise


async def _update_archive(db: AsyncSession, user_id: int, result: dict) -> None:
    """诊断完成 → 累计到档案."""
    res = await db.execute(select(Archive).where(Archive.user_id == user_id))
    archive = res.scalar_one_or_none()
    if not archive:
        import time, random, string
        archive = Archive(
            user_id=user_id,
            archive_no=f"VCT-A-{int(time.time())}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}",
            initial_baseline={"first_overall_score": result["overall_score"]},
        )
        db.add(archive)
        await db.flush()

    archive.total_diagnoses += 1
    archive.current_level = result.get("grade", archive.current_level)
