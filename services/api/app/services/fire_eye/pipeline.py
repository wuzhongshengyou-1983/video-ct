"""三步 Pipeline — Step1采集 → Step2分析 → Step3诊断"""
import asyncio
import logging
from .contracts import VideoCTContext
from .registry import registry

logger = logging.getLogger(__name__)


async def run_pipeline(video_url: str, diagnosis_id: str) -> VideoCTContext:
    """
    执行完整三步采集 + 诊断流水线。

    Step1: F1/F2/F3/F4 并行采集（各族独立超时，失败降级）
    Step2: 整理分析（数据校验 + 置信度合并）
    Step3: F5 CT诊断官（注入 Step1 上下文）

    Returns:
        VideoCTContext — 含 ct_report 的完整上下文
    """
    ctx = VideoCTContext(video_url=video_url, diagnosis_id=diagnosis_id)

    # Step1: 并行采集
    await _step1_collect(ctx)

    # Step2: 整理分析
    _step2_analyze(ctx)

    # Step3: CT 诊断
    await _step3_diagnose(ctx)

    return ctx


async def _step1_collect(ctx: VideoCTContext):
    """并行执行 F1/F2/F3/F4，失败的族记入 degraded_families"""
    collect_families = ["f1", "f2", "f3", "f4"]
    tasks = []

    for fam in collect_families:
        handler = registry.get(fam)
        if handler:
            timeout = registry._timeouts.get(fam, 15.0)
            tasks.append(_run_with_timeout(fam, handler, ctx, timeout))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def _run_with_timeout(family: str, handler, ctx: VideoCTContext, timeout: float):
    try:
        await asyncio.wait_for(handler(ctx), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"fire_eye: {family} timeout ({timeout}s), degraded")
        ctx.degraded_families.append(family)
    except Exception as e:
        logger.error(f"fire_eye: {family} error: {e}")
        ctx.degraded_families.append(family)
        ctx.errors.append({"family": family, "error": str(e)})


def _step2_analyze(ctx: VideoCTContext):
    """数据整理：校验置信度、补 fallback、格式化 prompt 输入"""
    # TODO: 实现置信度加权合并、缺失字段 fallback
    pass


async def _step3_diagnose(ctx: VideoCTContext):
    """调用 F5 CT诊断官"""
    handler = registry.get("f5")
    if handler:
        timeout = registry._timeouts.get("f5", 25.0)
        await _run_with_timeout("f5", handler, ctx, timeout)
