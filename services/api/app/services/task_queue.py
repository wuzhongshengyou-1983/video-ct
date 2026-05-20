"""Celery 异步任务队列 · 诊断 Pipeline 后台执行."""
from __future__ import annotations

from datetime import datetime, timezone

from celery import Celery, Task
from celery.result import AsyncResult
from loguru import logger
from sqlalchemy import select

from app.config import settings

# Celery app 初始化
celery_app = Celery(
    "video_ct",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,  # 结果后端也用 Redis
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # 任务完成后才 ack，防止进程崩溃丢任务
    worker_prefetch_multiplier=1,  # 公平调度
    task_default_retry_delay=60,
    task_max_retries=3,
    # 任务路由
    task_routes={
        "app.services.task_queue.run_diagnosis_pipeline": {"queue": "diagnosis"},
        "app.services.task_queue.fetch_competitor_data": {"queue": "crawler"},
    },
)


class CallbackTask(Task):
    """支持进度回调的 Celery Task 基类."""
    abstract = True

    def update_progress(self, diagnosis_id: int, pct: int, status: str | None = None) -> None:
        """更新任务进度（通过 Celery 的 state metadata）."""
        meta = {"diagnosis_id": diagnosis_id, "progress_pct": pct}
        if status:
            meta["status"] = status
        self.update_state(state="PROGRESS", meta=meta)


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.services.task_queue.run_diagnosis_pipeline",
    max_retries=3,
    default_retry_delay=120,
)
def run_diagnosis_pipeline(self, diagnosis_id: int) -> dict:
    """后台异步执行诊断 Pipeline.

    这个任务替代原来的 BackgroundTasks 方案，提供：
    - 进度回调（通过 WebSocket 推送给前端）
    - 自动重试（失败后最多 3 次）
    - 任务状态追踪（通过 Celery result backend）
    """
    import asyncio

    async def _run() -> dict:
        from app.database import session_scope
        from app.services.diagnosis_service import run_full_pipeline

        self.update_progress(diagnosis_id, 5, status="processing")

        try:
            async with session_scope() as db:
                self.update_progress(diagnosis_id, 10, status="fetching_meta")
                report = await run_full_pipeline(db, diagnosis_id)

                self.update_progress(diagnosis_id, 100, status="done")
                logger.info(f"[Celery] diagnosis_id={diagnosis_id} completed")

                return {
                    "diagnosis_id": diagnosis_id,
                    "report_id": report.id,
                    "overall_score": report.overall_score,
                    "grade": report.grade,
                    "model_used": report.model_used,
                    "cost_cents": report.cost_cents,
                }

        except Exception as exc:
            logger.exception(f"[Celery] diagnosis_id={diagnosis_id} failed: {exc}")
            self.update_progress(diagnosis_id, 0, status="failed")
            raise self.retry(exc=exc)

    # 在 Celery worker 线程中跑 asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 已在事件循环中，创建新任务
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(_run())
    except RuntimeError:
        return asyncio.run(_run())


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.services.task_queue.fetch_competitor_data",
    max_retries=2,
    default_retry_delay=300,
)
def fetch_competitor_data(self, track: str, platform: str = "douyin") -> dict:
    """异步抓取竞品/对标数据（预留）.

    生产环境应对接平台 API 或合规数据商。
    """
    logger.info(f"[Celery] fetch_competitor_data track={track} platform={platform}")
    # Mock 实现
    return {
        "track": track,
        "platform": platform,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sample_size": 50,
        "status": "mock_data",
        "note": "生产环境需接入真实数据源",
    }


def get_task_status(task_id: str) -> dict | None:
    """查询任务状态."""
    result = AsyncResult(task_id, app=celery_app)
    response: dict = {
        "task_id": task_id,
        "state": result.state,
    }
    if result.state == "PROGRESS" and result.info:
        response["progress"] = result.info
    elif result.state == "SUCCESS":
        response["result"] = result.result
    elif result.state == "FAILURE":
        response["error"] = str(result.info)
    return response
